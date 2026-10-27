from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score


ROOT = Path(__file__).parent
DATASET_PATH = ROOT / "dataset" / "student_data.csv"
MODEL_PATH = ROOT / "model" / "dropout_model.pkl"
IMPORTANCE_PATH = ROOT / "model" / "feature_importance.csv"
FEATURES = ["attendance", "study_hours", "previous_grade", "assignment_completion", "support_level", "absences"]


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError("Run generate_dataset.py before training the model.")
    frame = pd.read_csv(DATASET_PATH)
    train_x, test_x, train_y, test_y = train_test_split(
        frame[FEATURES], frame["dropout"], test_size=0.2, random_state=42, stratify=frame["dropout"]
    )
    model = RandomForestClassifier(n_estimators=180, max_depth=8, random_state=42, class_weight="balanced")
    model.fit(train_x, train_y)
    predictions = model.predict(test_x)
    probabilities = model.predict_proba(test_x)[:, 1]
    accuracy = accuracy_score(test_y, predictions)
    metrics = {
        "accuracy": round(float(accuracy), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(test_y, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(test_y, probabilities)), 4),
        "trained_on": len(frame),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "metrics": metrics}, MODEL_PATH)
    importance = pd.DataFrame({"feature": FEATURES, "importance": model.feature_importances_}).sort_values("importance", ascending=False)
    importance.to_csv(IMPORTANCE_PATH, index=False)
    print(f"Model trained with {accuracy:.1%} validation accuracy and {metrics['roc_auc']:.1%} ROC AUC")


if __name__ == "__main__":
    main()
