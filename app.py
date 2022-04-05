import logging
import uvicorn
import uvicorn.config
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from controllers.subscribe import router as subscribe_router
from controllers.cronjobs import *
import env

app = FastAPI()
app.include_router(subscribe_router)
logger = logging.getLogger(env.ENV_NAME)


@app.on_event('startup')
@repeat_every(seconds=300)
def trigger_fetch_parks_json():
    # condensed to one function due to bug in fastapi-utils
    # https://github.com/dmontagu/fastapi-utils/issues/256
    fetch_parks_json()
    fetch_wait_times_json()
    update_rides_table()


@app.on_event('startup')
@repeat_every(seconds=90)
def trigger_close_out_alerts():
    close_out_alerts()


if __name__ == '__main__':
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config['formatters']['access']['fmt'] = log_format
    log_config['formatters']['default']['fmt'] = log_format
    log_config['loggers'][env.ENV_NAME] = {'handlers':['default'], 'level':'DEBUG'}
    uvicorn.run(
        "app:app",
        host=env.API_HOST,
        port=int(env.API_PORT),
        log_config=log_config,
    )