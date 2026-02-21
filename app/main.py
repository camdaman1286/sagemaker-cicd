import os
import boto3
from botocore.config import Config
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Fraud Detection API")

ENDPOINT_NAME = os.environ["SAGEMAKER_ENDPOINT"]
REGION = os.environ.get("AWS_REGION", "us-east-1")
SAGEMAKER_ENDPOINT_URL = os.environ.get(
    "SAGEMAKER_ENDPOINT_URL",
    "https://172.31.28.9"
)

sagemaker_runtime = boto3.client(
    "sagemaker-runtime",
    region_name=REGION,
    endpoint_url=SAGEMAKER_ENDPOINT_URL,
    verify=False  # Skip SSL verification since we're using IP directly
)


class PredictionRequest(BaseModel):
    features: List[float]


class PredictionResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if len(request.features) != 30:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 30 features, got {len(request.features)}"
        )

    payload = ",".join(str(f) for f in request.features)

    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="text/csv",
            Accept="text/csv",
            Body=payload,
        )
        result = float(response["Body"].read().decode("utf-8"))
        return PredictionResponse(
            fraud_probability=result,
            is_fraud=result > 0.5
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
