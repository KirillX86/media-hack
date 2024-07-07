import joblib
import pandas as pd
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from etl import Clusterizer, DataPreprocessor

# Initialize FastAPI app
app = FastAPI()

# Define a request model to match the JSON structure
class TargetAudience(BaseModel):
    name: str
    gender: str
    ageFrom: int
    ageTo: int
    income: str

class Point(BaseModel):
    lat: str
    lon: str
    azimuth: int

class PredictionRequest(BaseModel):
    hash: str
    targetAudience: TargetAudience
    points: List[Point]


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
    # Convert points to DataFrame
    points_data = [{'lat': point.lat, 'lon': point.lon, 'azimuth': point.azimuth} for point in request.points]
    df_points = pd.DataFrame(points_data)

    # Prepare the data for preprocessing
    data = {
        'hash': request.hash,
        'targetAudience': request.targetAudience.dict(),
        'points': df_points.to_dict(orient='records')
    }
    df = pd.DataFrame([data])

    # Preprocess the data
    data_processed = processor.preprocess(df)

    # Extract features for prediction
    features = data_processed.values

    # Make prediction using the loaded model
    prediction = model.predict(features)

    return {"prediction": prediction[0]}


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
