from fastapi import FastAPI
from app.routes.transactions import router as transactions_router

app = FastAPI(title="Finance Tracker API")
app.include_router(transactions_router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
