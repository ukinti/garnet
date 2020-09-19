# Source: https://github.com/aiogram/aiogram

"""
This module has redis storage for user states based on`aioredis <https://github.com/aio-libs/aioredis>`_ driver
"""

import asyncio
import json
import logging
import typing

import aioredis

from garnet.storages.base import BaseStorage

STATE_KEY = "state"
STATE_DATA_KEY = "data"
STATE_BUCKET_KEY = "bucket"


class RedisStorage(BaseStorage):
    """
    Busted Redis-base storage for FSM.
    Works with Redis connection pool and customizable keys prefix.

    """

    def __init__(
        self,
        host: str = "localhost",
        port=6379,
        db=None,
        password=None,
        ssl=None,
        pool_size=10,
        loop=None,
        prefix="fsm",
        state_ttl: int = 0,
        data_ttl: int = 0,
        bucket_ttl: int = 0,
        **kwargs,
    ):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._pool_size = pool_size
        self._loop = loop or asyncio.get_event_loop()
        self._kwargs = kwargs
        self._prefix = (prefix,)

        self._state_ttl = state_ttl
        self._data_ttl = data_ttl
        self._bucket_ttl = bucket_ttl

        self._redis: aioredis.RedisConnection = None
        self._connection_lock = asyncio.Lock(loop=self._loop)

    async def redis(self) -> aioredis.Redis:
        """
        Get Redis connection
        """
        # Use thread-safe asyncio Lock because this method without that is not safe
        async with self._connection_lock:
            if self._redis is None:
                self._redis = await aioredis.create_redis_pool(
                    (self._host, self._port),
                    db=self._db,
                    password=self._password,
                    ssl=self._ssl,
                    minsize=1,
                    maxsize=self._pool_size,
                    loop=self._loop,
                    **self._kwargs,
                )
        return self._redis

    def generate_key(self, *parts):
        return ":".join(self._prefix + tuple(map(str, parts)))

    async def close(self):
        async with self._connection_lock:
            if self._redis and not self._redis.closed:
                self._redis.close()
                del self._redis
                self._redis = None

    async def wait_closed(self):
        async with self._connection_lock:
            if self._redis:
                return await self._redis.wait_closed()
            return True

    async def get_state(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        default: typing.Optional[str] = None,
    ) -> typing.Optional[str]:
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_KEY)
        redis = await self.redis()
        return await redis.get(key, encoding="utf8") or None

    async def get_data(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        default: typing.Optional[dict] = None,
    ) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_DATA_KEY)
        redis = await self.redis()
        raw_result = await redis.get(key, encoding="utf8")
        if raw_result:
            return json.loads(raw_result)
        return default or {}

    async def set_state(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        state: typing.Optional[typing.AnyStr] = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_KEY)
        redis = await self.redis()
        if state is None:
            await redis.delete(key)
        else:
            await redis.set(key, state, expire=self._state_ttl)

    async def set_data(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        data: typing.Dict = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_DATA_KEY)
        redis = await self.redis()
        await redis.set(key, json.dumps(data), expire=self._data_ttl)

    async def update_data(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        data: typing.Dict = None,
        **kwargs,
    ):
        if data is None:
            data = {}
        temp_data = await self.get_data(chat=chat, user=user, default={})
        temp_data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=temp_data)

    def has_bucket(self):
        return True

    async def get_bucket(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        default: typing.Optional[dict] = None,
    ) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_BUCKET_KEY)
        redis = await self.redis()
        raw_result = await redis.get(key, encoding="utf8")
        if raw_result:
            return json.loads(raw_result)
        return default or {}

    async def set_bucket(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        bucket: typing.Dict = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_BUCKET_KEY)
        redis = await self.redis()
        await redis.set(key, json.dumps(bucket), expire=self._bucket_ttl)

    async def update_bucket(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        bucket: typing.Dict = None,
        **kwargs,
    ):
        if bucket is None:
            bucket = {}
        temp_bucket = await self.get_bucket(chat=chat, user=user)
        temp_bucket.update(bucket, **kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=temp_bucket)

    async def reset_all(self, full=True):
        """
        Reset states in DB

        :param full: clean DB or clean only states
        :return:
        """
        conn = await self.redis()

        if full:
            await conn.flushdb()
        else:
            keys = await conn.keys(self.generate_key("*"))
            await conn.delete(*keys)

    async def get_states_list(self) -> typing.List[typing.Tuple[int, int]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        conn = await self.redis()
        result = []

        keys = await conn.keys(self.generate_key("*", "*", STATE_KEY), encoding="utf8")
        for item in keys:
            *_, chat, user, _ = item.split(":")
            result.append((chat, user))

        return result
