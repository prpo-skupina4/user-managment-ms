import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from models import Base
from api import get_db
import os
import tempfile

# Use a temporary file for testing database
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db.close()
TEST_DATABASE_URL = f"sqlite:///{temp_db.name}"
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Create a test client with a fresh database for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/auth/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_new_user(client):
    """Test registering a new user"""
    user_data = {
        "userId": 1,
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == user_data["email"]


def test_register_duplicate_user(client):
    """Test that registering a duplicate user fails"""
    user_data = {
        "userId": 2,
        "email": "duplicate@example.com",
        "password": "testpassword123"
    }
    # Register first time
    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code == 200
    
    # Try to register again
    response2 = client.post("/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()


def test_register_duplicate_user_id(client):
    """Test that registering with a duplicate userId fails"""
    # Register first user
    user_data1 = {
        "userId": 10,
        "email": "user1@example.com",
        "password": "testpassword123"
    }
    response1 = client.post("/auth/register", json=user_data1)
    assert response1.status_code == 200
    
    # Try to register another user with same userId but different email
    user_data2 = {
        "userId": 10,
        "email": "user2@example.com",
        "password": "testpassword456"
    }
    response2 = client.post("/auth/register", json=user_data2)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()


def test_register_invalid_email(client):
    """Test that registering with an invalid email fails"""
    user_data = {
        "userId": 3,
        "email": "not-an-email",
        "password": "testpassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_login_success(client):
    """Test successful login"""
    # First register a user
    user_data = {
        "userId": 4,
        "email": "login@example.com",
        "password": "testpassword123"
    }
    client.post("/auth/register", json=user_data)
    
    # Now try to login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Test login with wrong password"""
    # Register a user
    user_data = {
        "userId": 5,
        "email": "wrongpw@example.com",
        "password": "correctpassword"
    }
    client.post("/auth/register", json=user_data)
    
    # Try to login with wrong password
    login_data = {
        "username": user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401
    assert "invalid credentials" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "somepassword"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401


def test_me_endpoint_with_valid_token(client):
    """Test /me endpoint with a valid token"""
    # Register and login
    user_data = {
        "userId": 6,
        "email": "me@example.com",
        "password": "testpassword123"
    }
    client.post("/auth/register", json=user_data)
    
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    login_response = client.post("/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Access /me endpoint
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "sub" in data
    assert "exp" in data


def test_me_endpoint_without_token(client):
    """Test /me endpoint without authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_endpoint_with_invalid_token(client):
    """Test /me endpoint with an invalid token"""
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


def test_get_user_by_id(client):
    """Test getting a user by ID"""
    # Register a user
    user_data = {
        "userId": 7,
        "email": "getuser@example.com",
        "password": "testpassword123"
    }
    register_response = client.post("/auth/register", json=user_data)
    user_id = register_response.json()["id"]
    
    # Get user by ID
    response = client.get(f"/auth/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == user_data["email"]
    assert data["is_active"] is True


def test_get_nonexistent_user(client):
    """Test getting a non-existent user"""
    response = client.get("/auth/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_password_hashing(client):
    """Test that passwords are properly hashed and not stored in plain text"""
    from models import User
    from api import get_db
    
    # Register a user
    user_data = {
        "userId": 8,
        "email": "hash@example.com",
        "password": "mypassword123"
    }
    client.post("/auth/register", json=user_data)
    
    # Verify password is hashed in database
    db = next(override_get_db())
    user = db.query(User).filter(User.email == user_data["email"]).first()
    assert user is not None
    assert user.hashed_password != user_data["password"]
    assert len(user.hashed_password) > 50  # Bcrypt hashes are long
    db.close()


# Cleanup function to remove temporary database file
def teardown_module():
    """Clean up temporary database file after all tests"""
    try:
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)
    except Exception:
        pass
