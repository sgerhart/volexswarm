from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"agent": "optimize", "status": "running"}
