from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from routers.auth import auth_router
from routers.event import event_router
from routers.collaboration import collaboration_router
from routers.version import version_router
from routers.changelog import changelog_router
from database.connection import engine
from database.connection import Base
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import json
import msgpack

# Create a FastAPI instance
app = FastAPI()

# Create all tables (development only; need to use Alembic for production)
Base.metadata.create_all(bind=engine)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address, default_limits=["15/minute", "1000/day"])
app.state.limiter = limiter

# Register the rate limit exceeded handler
app.add_middleware(SlowAPIMiddleware)


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
app.include_router(version_router)
app.include_router(changelog_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}