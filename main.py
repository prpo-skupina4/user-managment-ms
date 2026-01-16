from fastapi import FastAPI
import api
from models import Base
from db import engine
from fastapi.middleware.cors import CORSMiddleware

def init():
    Base.metadata.create_all(bind=engine)


init()

app = FastAPI(title="FRITIME Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/auth")



