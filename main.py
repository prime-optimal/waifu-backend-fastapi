import logfire
from src.app import create_app

logfire.configure()
logfire.info('Hello, {name}!', name='world')

app = create_app()


@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}
