import uvicorn, env
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from controllers.subscribe import router as subscribe_router
from controllers.cronjobs import *

app = FastAPI()
app.include_router(subscribe_router)


@app.on_event('startup')
def startup():
    fetch_parks_json()
    fetch_wait_times_json()
    update_rides_table()


@repeat_every(seconds=604800)
def trigger_fetch_parks_json():
    fetch_parks_json()


@repeat_every(seconds=300)
def trigger_fetch_wait_times_json():
    fetch_wait_times_json()


@repeat_every(seconds=150)
def trigger_update_rides_table():
    update_rides_table()


@repeat_every(seconds=90)
def trigger_close_out_alerts():
    close_out_alerts()


if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host=env.API_HOST,
        port=int(env.API_PORT),
    )