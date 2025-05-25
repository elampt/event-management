import redis
from auth.config import settings

# Initialize Redis client
REDIS_URL = settings.redis_url
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

