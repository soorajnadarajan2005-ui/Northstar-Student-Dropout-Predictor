from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from database import init_db, prediction_summary, recent_predictions, save_prediction

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "model" / "dropout_model.pkl"
app = Flask(__name__, static_folder="static")
CORS(app)


def load_bundle():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run generate_dataset.py and train_model.py first.")
    return joblib.load(MODEL_PATH)


def risk_level(probability: float) -> str:
    return "High" if probability >= 0.65 else "Medium" if probability >= 0.35 else "Low"


def signal_details(values: dict[str, float], bundle: dict) -> list[dict[str, str]]:
    labels = {
        "attendance": ("Attendance", 75, "lower attendance"),
        "study_hours": ("Study time", 8, "limited study time"),
        "previous_grade": ("Previous grade", 65, "lower previous grade"),
        "assignment_completion": ("Assignment completion", 70, "incomplete assignments"),
        "support_level": ("Support level", 3, "limited support"),
        "absences": ("Absences", 5, "frequent absences"),
    }
    ranked = []
    for feature, importance in zip(bundle["features"], bundle["model"].feature_importances_):
        label, baseline, concern = labels[feature]
        value = values[feature]
        is_concern = value < baseline if feature != "absences" else value > baseline
        distance = abs(value - baseline) / max(abs(baseline), 1)
        ranked.append({"label": label, "impact": "Elevates risk" if is_concern else "Protective signal", "detail": concern if is_concern else "within a healthy range", "score": float(importance * distance)})
    return sorted(ranked, key=lambda item: item["score"], reverse=True)[:3]


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/recent")
def recent():
    return jsonify(recent_predictions())


@app.get("/api/overview")
def overview():
    bundle = load_bundle()
    dataset = pd.read_csv(ROOT / "dataset" / "student_data.csv")
    elevated = int(dataset["dropout"].sum())
    return jsonify({
        "students": len(dataset),
        "elevated_risk": elevated,
        "elevated_rate": round(elevated / len(dataset), 3),
        "metrics": bundle.get("metrics", {}),
        "prediction_summary": prediction_summary(),
        "features": [{"name": name, "importance": round(float(value), 3)} for name, value in zip(bundle["features"], bundle["model"].feature_importances_)],
    })


@app.post("/api/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    try:
        values = {
            "attendance": float(payload["attendance"]),
            "study_hours": float(payload["study_hours"]),
            "previous_grade": float(payload["previous_grade"]),
            "assignment_completion": float(payload["assignment_completion"]),
            "support_level": float(payload["support_level"]),
            "absences": float(payload["absences"]),
        }
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Please provide every student metric as a number."}), 400
    bounds = {"attendance": (0, 100), "study_hours": (0, 40), "previous_grade": (0, 100), "assignment_completion": (0, 100), "support_level": (1, 5), "absences": (0, 40)}
    if any(not lower <= values[name] <= upper for name, (lower, upper) in bounds.items()):
        return jsonify({"error": "One or more values are outside the allowed range."}), 400
    student_name = str(payload.get("student_name") or "New student").strip()[:80]
    if not student_name:
        return jsonify({"error": "Please enter a student name."}), 400

    bundle = load_bundle()
    features = bundle["features"]
    row = pd.DataFrame([[values[feature] for feature in features]], columns=features)
    model = bundle["model"]
    probability = float(model.predict_proba(row)[0][1])
    level = risk_level(probability)
    save_prediction(student_name, level, probability)
    actions = {"High": "Schedule a support conversation within 48 hours.", "Medium": "Check in this week and monitor attendance and assignments.", "Low": "Keep the current support rhythm and reassess next month."}
    return jsonify({"student_name": student_name, "risk_level": level, "probability": round(probability, 4), "confidence": round(abs(probability - 0.5) * 2, 3), "signals": signal_details(values, bundle), "recommended_action": actions[level], "recent": recent_predictions()})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
