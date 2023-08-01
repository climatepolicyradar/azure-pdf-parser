from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def get_health():
    """
    Get application health.

    TODO: fill in implementation with real health check.
    """
    return {"status": "OK"}
