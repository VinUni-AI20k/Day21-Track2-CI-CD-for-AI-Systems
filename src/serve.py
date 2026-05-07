from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import joblib
import os

app = FastAPI()

S3_BUCKET = os.environ["S3_BUCKET"]
S3_MODEL_KEY = "models/latest/model.pkl"
MODEL_PATH = os.path.expanduser("~/models/model.pkl")


def download_model():
    """
    Tai file model.pkl tu S3 ve may khi server khoi dong.
    Su dung AWS credentials tu IAM role (hoac bien moi truong).
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    s3 = boto3.client("s3")
    s3.download_file(S3_BUCKET, S3_MODEL_KEY, MODEL_PATH)
    print(f"Model downloaded from s3://{S3_BUCKET}/{S3_MODEL_KEY} to {MODEL_PATH}")


download_model()
model = joblib.load(MODEL_PATH)


class PredictRequest(BaseModel):
    features: list[float]


@app.get("/health")
def health():
    """
    Endpoint kiem tra suc khoe server.
    GitHub Actions goi endpoint nay sau khi deploy de xac nhan server dang chay.

    Tra ve: {"status": "ok"}
    """
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest):
    """
    Endpoint suy luan chinh.

    Dau vao : JSON {"features": [f1, f2, ..., f12]}
    Dau ra  : JSON {"prediction": <0|1|2>, "label": <"thap"|"trung_binh"|"cao">}

    Thu tu 12 dac trung (khop voi thu tu trong FEATURE_NAMES):
        fixed_acidity, volatile_acidity, citric_acid, residual_sugar,
        chlorides, free_sulfur_dioxide, total_sulfur_dioxide, density,
        pH, sulphates, alcohol, wine_type
    """
    # Kiem tra so luong dac trung
    if len(req.features) != 12:
        raise HTTPException(
            status_code=400,
            detail="Expected 12 features (wine quality) but got "
            f"{len(req.features)}"
        )

    # Goi model.predict de lay ket qua du doan
    pred = model.predict([req.features])[0]

    # Map label
    LABEL_MAP = {0: "thap", 1: "trung_binh", 2: "cao"}
    label = LABEL_MAP.get(int(pred), "unknown")

    return {"prediction": int(pred), "label": label}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
