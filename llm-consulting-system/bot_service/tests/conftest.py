import pytest
from fakeredis.aioredis import FakeRedis


@pytest.fixture
async def fake_redis():
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.aclose()