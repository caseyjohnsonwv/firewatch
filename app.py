import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import uvicorn
import uvicorn.config
from fastapi import FastAPI
from controllers.subscribe import router as subscribe_router
from controllers.cronjobs import *
import env


app = FastAPI()
app.include_router(subscribe_router)
logger = logging.getLogger(env.ENV_NAME)


# set up background tasks
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_parks_json, CronTrigger.from_crontab('0 0 * * MON'))
scheduler.add_job(update_wait_times, CronTrigger.from_crontab('1/5 * * * *'))
scheduler.add_job(close_out_alerts, CronTrigger.from_crontab('3/5 * * * *'))


# define startup tasks
@app.on_event('startup')
def startup():
    fetch_parks_json()
    update_wait_times()
    scheduler.start()


@app.get('/', status_code=200)
def healthcheck():
    pass


if __name__ == '__main__':
    # override built-in logging
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config['formatters']['access']['fmt'] = log_format
    log_config['formatters']['default']['fmt'] = log_format
    log_config['loggers'][env.ENV_NAME] = {'handlers':['default'], 'level':env.LOG_LEVEL}
    # run application
    uvicorn.run(
        'app:app',
        host=env.API_HOST,
        port=env.API_PORT,
        log_config=log_config,
    )
