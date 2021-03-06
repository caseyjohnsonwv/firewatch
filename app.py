import datetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import uvicorn
import uvicorn.config
from fastapi import FastAPI
from controllers.subscribe import live_router, test_router
from controllers.cronjobs import *
import env


app = FastAPI()
app.include_router(live_router)
if env.ENV_NAME == 'local':
    app.include_router(test_router)


logger = logging.getLogger('uvicorn')


# set up background tasks
scheduler = BackgroundScheduler()
fetch_job = scheduler.add_job(fetch_parks_json, CronTrigger.from_crontab('0 0 * * MON'))
update_job = scheduler.add_job(update_wait_times, CronTrigger.from_crontab('1/5 * * * *'))
close_job = scheduler.add_job(close_out_alerts, CronTrigger.from_crontab('0/5 * * * *'))


# define startup tasks
@app.on_event('startup')
def startup():
    scheduler.modify_job(fetch_job.id, next_run_time=datetime.datetime.now())
    scheduler.modify_job(update_job.id, next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10))
    scheduler.start()


if __name__ == '__main__':
    # run application
    if env.ENV_NAME == 'local':
        uvicorn.run(
            'app:app',
            host='localhost',
            port=5000,
        )