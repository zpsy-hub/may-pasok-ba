from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="new-capstone web")

class Health(BaseModel):
    status: str


@app.get("/", response_model=Health)
async def root():
    return {"status": "ok"}


@app.get("/predict")
async def predict():
    # Placeholder: load model/artifact and return a demo response
    return {"prediction": 1, "confidence": 0.9}
