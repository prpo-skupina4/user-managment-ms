from fastapi import FastAPI
import api
from models import Base
from db import engine


def init():
    Base.metadata.create_all(bind=engine)


init()

app = FastAPI(title="FRITIME Auth Service")

app.include_router(api.router, prefix="/auth")
