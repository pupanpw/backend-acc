from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.transactions import router as transactions_router

app = FastAPI(title="Finance Tracker API")

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include router
app.include_router(transactions_router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
