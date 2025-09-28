import redis.asyncio as redis
import os
from dotenv import load_dotenv
import asyncio
from core.utils.logger import logger
from typing import List, Any, Callable, Awaitable, TypeVar
from core.utils.retry import retry
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
    BusyLoadingError,
)

T = TypeVar("T")

# Redis client and connection pool
client: redis.Redis | None = None
pool: redis.ConnectionPool | None = None
_initialized = False
_init_lock = asyncio.Lock()

_CONNECTION_ERRORS = (
    RedisConnectionError,
    RedisTimeoutError,
    BusyLoadingError,
    ConnectionResetError,
    BrokenPipeError,
)

# Constants
REDIS_KEY_TTL = 3600 * 24  # 24 hour TTL as safety mechanism


def initialize():
    """Initialize Redis connection pool and client using environment variables."""
    global client, pool

    # Load environment variables if not already loaded
    load_dotenv()

    # Get Redis configuration
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD", "")
    
    # Connection pool configuration - optimized for production
    max_connections = 128            # Reasonable limit for production
    socket_timeout = 15.0            # 15 seconds socket timeout
    connect_timeout = 10.0           # 10 seconds connection timeout
    retry_on_timeout = not (os.getenv("REDIS_RETRY_ON_TIMEOUT", "True").lower() != "true")

    logger.debug(f"Initializing Redis connection pool to {redis_host}:{redis_port} with max {max_connections} connections")

    # Create connection pool with production-optimized settings
    pool = redis.ConnectionPool(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
        socket_timeout=socket_timeout,
        socket_connect_timeout=connect_timeout,
        socket_keepalive=True,
        retry_on_timeout=retry_on_timeout,
        health_check_interval=30,
        max_connections=max_connections,
    )

    # Create Redis client from connection pool
    client = redis.Redis(connection_pool=pool)

    return client


async def initialize_async():
    """Initialize Redis connection asynchronously."""
    global client, _initialized

    async with _init_lock:
        if not _initialized:
            logger.debug("Initializing Redis connection")
            initialize()

        try:
            # Test connection with timeout
            await asyncio.wait_for(client.ping(), timeout=5.0)
            logger.debug("Successfully connected to Redis")
            _initialized = True
        except asyncio.TimeoutError:
            logger.error("Redis connection timeout during initialization")
            client = None
            _initialized = False
            raise ConnectionError("Redis connection timeout")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            client = None
            _initialized = False
            raise

    return client


async def close():
    """Close Redis connection and connection pool."""
    global client, pool, _initialized
    if client:
        logger.debug("Closing Redis connection")
        try:
            await asyncio.wait_for(client.aclose(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Redis close timeout, forcing close")
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")
        finally:
            client = None
    
    if pool:
        logger.debug("Closing Redis connection pool")
        try:
            await asyncio.wait_for(pool.aclose(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Redis pool close timeout, forcing close")
        except Exception as e:
            logger.warning(f"Error closing Redis pool: {e}")
        finally:
            pool = None
    
    _initialized = False
    logger.debug("Redis connection and pool closed")


async def get_client():
    """Get the Redis client, initializing if necessary."""
    global client, _initialized
    if client is None or not _initialized:
        await retry(lambda: initialize_async())
    return client


async def _execute_with_reconnect(
    operation: Callable[[redis.Redis], Awaitable[T]],
    *,
    op_name: str,
    retries: int = 2,
) -> T:
    """Execute a Redis operation with automatic reconnection on connection errors."""
    attempt = 0
    last_error: Exception | None = None

    while attempt <= retries:
        redis_client = await get_client()

        try:
            return await operation(redis_client)
        except _CONNECTION_ERRORS as error:
            last_error = error
            attempt += 1
            logger.warning(
                f"Redis operation '{op_name}' failed due to connection issue (attempt {attempt}/{retries + 1}): {error}"
            )
            # Reset the client and pool so the next attempt forces a reconnect
            await close()

            if attempt <= retries:
                backoff = min(0.5 * (2 ** (attempt - 1)), 5.0)
                await asyncio.sleep(backoff)
                continue
        except Exception as error:  # pragma: no cover - pass through unexpected errors
            raise error

        break

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        f"Redis operation '{op_name}' failed without an associated connection error"
    )


# Basic Redis operations
async def set(key: str, value: str, ex: int = None, nx: bool = False):
    """Set a Redis key."""
    async def _operation(redis_client: redis.Redis):
        return await redis_client.set(key, value, ex=ex, nx=nx)

    return await _execute_with_reconnect(_operation, op_name="set")


async def get(key: str, default: str = None):
    """Get a Redis key."""
    async def _operation(redis_client: redis.Redis):
        return await redis_client.get(key)

    result = await _execute_with_reconnect(_operation, op_name="get")
    return result if result is not None else default


async def delete(key: str):
    """Delete a Redis key."""
    async def _operation(redis_client: redis.Redis):
        return await redis_client.delete(key)

    return await _execute_with_reconnect(_operation, op_name="delete")


async def publish(channel: str, message: str):
    """Publish a message to a Redis channel."""
    async def _operation(redis_client: redis.Redis):
        return await redis_client.publish(channel, message)

    return await _execute_with_reconnect(_operation, op_name="publish")


async def create_pubsub():
    """Create a Redis pubsub object."""
    async def _operation(redis_client: redis.Redis):
        return redis_client.pubsub()

    return await _execute_with_reconnect(_operation, op_name="create_pubsub")


# List operations
async def rpush(key: str, *values: Any):
    """Append one or more values to a list."""
    async def _operation(redis_client: redis.Redis):
        return await redis_client.rpush(key, *values)

    return await _execute_with_reconnect(_operation, op_name="rpush")


async def lrange(key: str, start: int, end: int) -> List[str]:
    """Get a range of elements from a list."""
    async def _operation(redis_client: redis.Redis):
        return await redis_client.lrange(key, start, end)

    return await _execute_with_reconnect(_operation, op_name="lrange")


# Key management


async def keys(pattern: str) -> List[str]:
    async def _operation(redis_client: redis.Redis):
        return await redis_client.keys(pattern)

    return await _execute_with_reconnect(_operation, op_name="keys")


async def expire(key: str, seconds: int):
    async def _operation(redis_client: redis.Redis):
        return await redis_client.expire(key, seconds)

    return await _execute_with_reconnect(_operation, op_name="expire")
