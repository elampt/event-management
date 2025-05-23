from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from routers.auth import router as auth_router
from routers.event import router as event_router
from routers.collaboration import router as collaboration_router
from database.connection import engine
from database.connection import Base
import json
import msgpack

# Create a FastAPI instance
app = FastAPI()

# Create all tables (development only; need to use Alembic for production)
Base.metadata.create_all(bind=engine)

# Middleware for Message Pack response
@app.middleware("http")
async def msgpack_middleware(request: Request, call_next):
    response = await call_next(request)
    accept = request.headers.get("accept", "")
    if "application/msgpack" in accept:
        # Get the JSON data from the response
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        # Decode JSON to dict, then encode as msgpack
        dict_data = json.loads(body)
        msgpack_bytes = msgpack.packb(dict_data, use_bin_type=True)
        return Response(content=msgpack_bytes, media_type="application/msgpack")
    return response



# Include the routers
app.include_router(auth_router)
app.include_router(event_router)
app.include_router(collaboration_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}