import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import tempfile

# Set testing mode before importing main
os.environ["TESTING"] = "1"

from main import app
from models import Base
from api import get_db

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
    response = client.post("/auth/users", json=user_data)
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
    response1 = client.post("/auth/users", json=user_data)
    assert response1.status_code == 200
    
    # Try to register again
    response2 = client.post("/auth/users", json=user_data)
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
    response1 = client.post("/auth/users", json=user_data1)
    assert response1.status_code == 200
    
    # Try to register another user with same userId but different email
    user_data2 = {
        "userId": 10,
        "email": "user2@example.com",
        "password": "testpassword456"
    }
    response2 = client.post("/auth/users", json=user_data2)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()


def test_register_invalid_email(client):
    """Test that registering with an invalid email fails"""
    user_data = {
        "userId": 3,
        "email": "not-an-email",
        "password": "testpassword123"
    }
    response = client.post("/auth/users", json=user_data)
    assert response.status_code == 422  # Validation error


def test_login_success(client):
    """Test successful login"""
    # First register a user
    user_data = {
        "userId": 4,
        "email": "login@example.com",
        "password": "testpassword123"
    }
    client.post("/auth/users", json=user_data)
    
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
    client.post("/auth/users", json=user_data)
    
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
    client.post("/auth/users", json=user_data)
    
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    login_response = client.post("/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Access /me endpoint
    response = client.get("/auth/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "sub" in data
    assert "exp" in data


def test_me_endpoint_without_token(client):
    """Test /me endpoint without authentication"""
    response = client.get("/auth/users/me")
    assert response.status_code == 401


def test_me_endpoint_with_invalid_token(client):
    """Test /me endpoint with an invalid token"""
    response = client.get("/auth/users/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


def test_get_user_by_id(client):
    """Test getting a user by ID"""
    # Register a user
    user_data = {
        "userId": 7,
        "email": "getuser@example.com",
        "password": "testpassword123"
    }
    register_response = client.post("/auth/users", json=user_data)
    user_id = register_response.json()["id"]
    
    # Get user by ID
    response = client.get(f"/auth/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == user_data["email"]
    assert data["is_active"] is True


def test_get_nonexistent_user(client):
    """Test getting a non-existent user"""
    response = client.get("/auth/users/99999")
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
    client.post("/auth/users", json=user_data)
    
    # Verify password is hashed in database
    db = next(override_get_db())
    user = db.query(User).filter(User.email == user_data["email"]).first()
    assert user is not None
    assert user.hashed_password != user_data["password"]
    assert len(user.hashed_password) > 50  # Bcrypt hashes are long
    db.close()


def test_add_friend(client):
    """Test adding a friend"""
    # Register two users
    user1_data = {
        "userId": 100,
        "email": "user1@example.com",
        "password": "password123"
    }
    user2_data = {
        "userId": 101,
        "email": "user2@example.com",
        "password": "password123"
    }
    client.post("/auth/users", json=user1_data)
    client.post("/auth/users", json=user2_data)
    
    # Add friend
    friend_data = {
        "friend_id": 101,
        "name": "Friend Name"
    }
    response = client.post("/auth/users/100/friends", json=friend_data)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 100
    assert data["friend_id"] == 101
    assert data["name"] == "Friend Name"


def test_add_friend_nonexistent_user(client):
    """Test adding a friend with nonexistent user"""
    friend_data = {
        "friend_id": 998,
        "name": "Friend Name"
    }
    response = client.post("/auth/users/999/friends", json=friend_data)
    assert response.status_code == 404


def test_add_duplicate_friend(client):
    """Test adding a friend that already exists"""
    # Register two users
    user1_data = {
        "userId": 200,
        "email": "user200@example.com",
        "password": "password123"
    }
    user2_data = {
        "userId": 201,
        "email": "user201@example.com",
        "password": "password123"
    }
    client.post("/auth/users", json=user1_data)
    client.post("/auth/users", json=user2_data)
    
    # Add friend first time
    friend_data = {
        "friend_id": 201,
        "name": "Friend Name"
    }
    response1 = client.post("/auth/users/200/friends", json=friend_data)
    assert response1.status_code == 200
    
    # Try to add again
    response2 = client.post("/auth/users/200/friends", json=friend_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()


def test_list_friends(client):
    """Test listing friends"""
    # Register users
    user1_data = {
        "userId": 300,
        "email": "user300@example.com",
        "password": "password123"
    }
    user2_data = {
        "userId": 301,
        "email": "user301@example.com",
        "password": "password123"
    }
    user3_data = {
        "userId": 302,
        "email": "user302@example.com",
        "password": "password123"
    }
    client.post("/auth/users", json=user1_data)
    client.post("/auth/users", json=user2_data)
    client.post("/auth/users", json=user3_data)
    
    # Add friends
    client.post("/auth/users/300/friends", json={
        "friend_id": 301,
        "name": "Friend 1"
    })
    client.post("/auth/users/300/friends", json={
        "friend_id": 302,
        "name": "Friend 2"
    })
    
    # List friends (now returns paginated response)
    response = client.get("/auth/users/300/friends")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert any(f["friend_id"] == 301 and f["name"] == "Friend 1" for f in data["items"])
    assert any(f["friend_id"] == 302 and f["name"] == "Friend 2" for f in data["items"])


def test_list_friends_nonexistent_user(client):
    """Test listing friends for nonexistent user"""
    response = client.get("/auth/users/999/friends")
    assert response.status_code == 404


def test_list_friends_pagination(client):
    """Test friends pagination with skip and limit"""
    # Register users
    client.post("/auth/users", json={"userId": 400, "email": "user400@example.com", "password": "pass123"})
    for i in range(1, 6):  # Create 5 friends
        client.post("/auth/users", json={"userId": 400 + i, "email": f"user{400 + i}@example.com", "password": "pass123"})
        client.post("/auth/users/400/friends", json={"friend_id": 400 + i, "name": f"Friend {i}"})
    
    # Test first page
    response = client.get("/auth/users/400/friends?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2
    
    # Test second page
    response = client.get("/auth/users/400/friends?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 2
    
    # Test last page
    response = client.get("/auth/users/400/friends?skip=4&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 1  # Only 1 item left
    assert data["skip"] == 4


def test_list_friends_pagination_empty(client):
    """Test pagination with user that has no friends"""
    client.post("/auth/users", json={"userId": 500, "email": "user500@example.com", "password": "pass123"})
    
    response = client.get("/auth/users/500/friends")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert data["skip"] == 0
    assert data["limit"] == 10  # Default limit


def test_list_friends_pagination_custom_limit(client):
    """Test pagination with custom limit"""
    # Register users
    client.post("/auth/users", json={"userId": 600, "email": "user600@example.com", "password": "pass123"})
    for i in range(1, 4):  # Create 3 friends
        client.post("/auth/users", json={"userId": 600 + i, "email": f"user{600 + i}@example.com", "password": "pass123"})
        client.post("/auth/users/600/friends", json={"friend_id": 600 + i, "name": f"Friend {i}"})
    
    # Test with custom limit
    response = client.get("/auth/users/600/friends?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 1
    assert data["limit"] == 1


def test_list_friends_pagination_invalid_skip(client):
    """Test pagination with invalid skip parameter"""
    client.post("/auth/users", json={"userId": 700, "email": "user700@example.com", "password": "pass123"})
    
    response = client.get("/auth/users/700/friends?skip=-1")
    assert response.status_code == 400
    assert "skip" in response.json()["detail"].lower()


def test_list_friends_pagination_invalid_limit(client):
    """Test pagination with invalid limit parameter"""
    client.post("/auth/users", json={"userId": 800, "email": "user800@example.com", "password": "pass123"})
    
    # Test limit < 1
    response = client.get("/auth/users/800/friends?limit=0")
    assert response.status_code == 400
    assert "limit" in response.json()["detail"].lower()
    
    # Test limit > 100
    response = client.get("/auth/users/800/friends?limit=101")
    assert response.status_code == 400
    assert "limit" in response.json()["detail"].lower()


# Cleanup function to remove temporary database file
def teardown_module():
    """Clean up temporary database file after all tests"""
    try:
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)
    except Exception:
        pass
