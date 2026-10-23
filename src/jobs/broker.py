from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from core import settings, setup_logging

setup_logging()
broker = ListQueueBroker(settings.REDIS_URL).with_result_backend(
    RedisAsyncResultBackend(settings.REDIS_URL)
)
