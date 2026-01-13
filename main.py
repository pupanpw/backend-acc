from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.transactions import router as transactions_router
from app.routes.users import router as user_router
from app.routes.periodSummary import router as period_summary

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
# app.include_router(user_router)
app.include_router(period_summary)


@app.get("/")
def read_root():
    return {"message": "OK"}
