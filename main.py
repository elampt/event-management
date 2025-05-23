from fastapi import FastAPI, Request, Response
from routers.auth import router as auth_router
from routers.event import router as event_router
from database.connection import engine
from database.connection import Base

# Create a FastAPI instance
app = FastAPI()

# Create all tables (development only; need to use Alembic for production)
Base.metadata.create_all(bind=engine)

# Include the routers
app.include_router(auth_router)
app.include_router(event_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}