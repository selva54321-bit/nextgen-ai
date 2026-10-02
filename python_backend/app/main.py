from pathlib import Path

import joblib

from fastapi import FastAPI, HTTPException

from catboost import CatBoostClassifier, Pool

from app.schemas import (
    PredictionRequest,
    PredictionResponse
)

from app.feature_builder import derive_features

from app.explain import get_top_factors


# =========================================================
# Configuration
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"

CATBOOST_PATH = MODEL_DIR / "first_attempt_failure_catboost.cbm"
ISOTONIC_PATH = MODEL_DIR / "first_attempt_failure_isotonic.joblib"
METADATA_PATH = MODEL_DIR / "first_attempt_failure_metadata.joblib"

TOP_K_FACTORS = 3


# =========================================================
# Load models once when API starts
# =========================================================

cat_model = CatBoostClassifier()
cat_model.load_model(str(CATBOOST_PATH))

iso_model = joblib.load(ISOTONIC_PATH)

metadata = joblib.load(METADATA_PATH)

FEATURES = metadata["features"]
CAT_FEATURES = metadata["categorical_features"]


# =========================================================
# FastAPI
# =========================================================

app = FastAPI(
    title="Selva First Attempt Failure API",
    version="1.0.0"
)


# =========================================================
# Helpers
# =========================================================

def risk_band_for(probability: float) -> str:

    if probability < 0.01:
        return "LOW"

    if probability < 0.05:
        return "MEDIUM"

    return "HIGH"


def risk_increasing_factors(pool: Pool, top_k: int):
    """
    explain.get_top_factors ranks by |SHAP|, so its output can include
    features that REDUCE risk, while the descriptions in explain.py are
    all written as risk-raising explanations. Request every feature,
    keep only the ones that push risk up, then take the top_k.
    """

    all_factors = get_top_factors(
        cat_model,
        pool,
        FEATURES,
        top_k=len(FEATURES)
    )

    increasing = [
        f for f in all_factors
        if f["impact"] == "increases_risk"
    ]

    return increasing[:top_k]


# =========================================================
# Health Check
# =========================================================

@app.get("/")
def root():

    return {
        "service": "First Attempt Failure Engine",
        "status": "running"
    }


# =========================================================
# Prediction
# =========================================================

@app.post(
    "/predict",
    response_model=PredictionResponse
)
def predict(request: PredictionRequest):

    try:

        # 1. Derive model features from raw input
        X = derive_features(request)

        # Exact training feature order
        X = X[FEATURES]

        # 2. CatBoost Pool
        pool = Pool(
            X,
            cat_features=CAT_FEATURES
        )

        # 3. Raw CatBoost probability
        raw_probability = float(
            cat_model.predict_proba(pool)[0][1]
        )

        # 4. Isotonic calibration, clipped to [0, 1]
        calibrated_probability = float(
            iso_model.predict([raw_probability])[0]
        )

        calibrated_probability = max(
            0.0,
            min(1.0, calibrated_probability)
        )

        # 5. Risk band
        risk_band = risk_band_for(calibrated_probability)

        # 6. Explanation (risk-increasing factors only)
        top_factors = risk_increasing_factors(
            pool,
            TOP_K_FACTORS
        )

        # 7. Response
        return {
            "failure_probability": round(calibrated_probability, 4),
            "risk_band": risk_band,
            "top_factors": top_factors
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )