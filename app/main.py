from fastapi import FastAPI
from app.api import auth, users
from app.init_db import init

app = FastAPI(title="FRITIME Auth Service")

init()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
