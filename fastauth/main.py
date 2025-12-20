from fastapi import FastAPI

app = FastAPI(title="FastAuth")

@app.get("/health")
def health():
    return {"status": "ok"}
