from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import pandas as pd
import joblib
import pickle
from typing import List
from etl import Clusterizer, DataPreprocessor

# Initialize FastAPI app
app = FastAPI()


# Define a request model
class PredictionRequest(BaseModel):
    hash: str
    targetAudience: dict
    points: List


# Define a response model
class PredictionResponse(BaseModel):
    prediction: float


# Load data transformations
clusterizer = Clusterizer()
processor = DataPreprocessor(clusterizer=clusterizer)

# Load the saved pipeline
model = joblib.load('regressor_model.joblib')


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """
    Prediction endpoint
    :param request:
    :return:
    """
    data = pd.read_json(request, typ='series').to_frame().T
    data_processed = processor.preprocess(df=data)
    prediction = model.predict(data_processed)
    return {"prediction": prediction}


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
