try:
    import logfire

    logfire.configure()
    logfire.info("Hello, {name}!", name="world")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Logfire not available, using standard logging")

from src.app import create_app

app = create_app()


@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}
