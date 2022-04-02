import uvicorn, env
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from controllers.subscribe import router as subscribe_router
from controllers.cronjobs import fetch_parks_json, fetch_wait_times_json

app = FastAPI()
app.include_router(subscribe_router)


@app.on_event('startup')
def startup():
    fetch_parks_json()
    fetch_wait_times_json()


@repeat_every(seconds=604800)
def update_parks():
    fetch_parks_json()


@repeat_every(seconds=300)
def update_wait_times():
    fetch_wait_times_json()


if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host=env.API_HOST,
        port=int(env.API_PORT),
        reload=True if env.API_HOST == 'localhost' else False,
    )