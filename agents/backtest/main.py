from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"agent": "backtest", "status": "running"}
