import uvicorn, env
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.cronjobs import fetch_parks_json
from controllers.subscribe import router as subscribe_router

app = FastAPI()
app.include_router(subscribe_router)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.on_event('startup')
async def execute_startup_tasks():
    await fetch_parks_json()


if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host=env.API_HOST,
        port=int(env.API_PORT),
        reload=True if env.API_HOST == 'localhost' else False,
    )