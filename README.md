# Northstar Student Dropout Predictor

A small Flask dashboard that estimates student dropout risk from six academic and engagement signals. It uses a reproducible synthetic dataset and a Random Forest classifier, then stores assessment history in SQLite.

The dashboard includes live cohort statistics, balanced model-quality metrics, feature importance, confidence, explainable risk signals, recommended support actions, input validation, responsive layouts, and CSV export for recent assessments. The interface is decision support, not an automated decision-maker.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_dataset.py
python train_model.py
python main.py
```

Open http://127.0.0.1:5000 in a browser.

## Project layout

- `generate_dataset.py` creates `dataset/student_data.csv` with 600 sample records.
- `train_model.py` trains `model/dropout_model.pkl` and exports `model/feature_importance.csv`.
- `database.py` initializes `database/students.db` and persists predictions.
- `main.py` serves the dashboard and `/api/predict` and `/api/recent` endpoints.
- `/api/overview` serves live cohort statistics, validation metrics, and feature importance.
- `static/` contains the responsive dashboard UI.

The generated dataset is synthetic and intended for development or demonstration, not real student decisions.
