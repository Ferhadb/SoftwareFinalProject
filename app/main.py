from fastapi import FastAPI
from app.web.router import router as web_router

app = FastAPI(title="SpendSmart")
@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(web_router)
