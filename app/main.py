from fastapi import FastAPI

app = FastAPI(title="SpendSmart")


@app.get("/health")
def health():
    return {"status": "ok"}
