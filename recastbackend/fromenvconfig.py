import os
CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = os.environ['CELERY_REDIS_HOST']
CELERY_REDIS_PORT = os.environ['CELERY_REDIS_PORT']
CELERY_REDIS_DB = os.environ['CELERY_REDIS_DB']
CELERY_IMPORTS = ('recastbackend.backendtasks',)
CELERY_TRACK_STARTED = True
BROKER_URL = 'redis://{}'.format(CELERY_REDIS_HOST)