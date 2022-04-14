import datetime
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
fetch_job = scheduler.add_job(fetch_parks_json, CronTrigger.from_crontab('0 0 * * MON'))
update_job = scheduler.add_job(update_wait_times, CronTrigger.from_crontab('1/5 * * * *'))
close_job = scheduler.add_job(close_out_alerts, CronTrigger.from_crontab('3/5 * * * *'))


# define startup tasks
@app.on_event('startup')
def startup():
    scheduler.modify_job(fetch_job.id, next_run_time=datetime.datetime.now())
    scheduler.modify_job(update_job.id, next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10))
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
    if env.ENV_NAME == 'local':
        uvicorn.run(
            'app:app',
            host='localhost',
            port=5000,
            log_config=log_config,
        )
    else:
        app.docs_url = None
        app.redoc_url = None