from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).parent
DATASET_PATH = ROOT / "dataset" / "student_data.csv"


def main() -> None:
    rng = np.random.default_rng(42)
    count = 600
    attendance = np.clip(rng.normal(78, 13, count), 35, 100)
    study_hours = np.clip(rng.normal(11, 5, count), 1, 30)
    previous_grade = np.clip(rng.normal(68, 14, count), 20, 100)
    assignments = np.clip(rng.normal(76, 15, count), 20, 100)
    support = rng.integers(1, 6, count)
    absences = np.clip(np.rint((100 - attendance) / 3 + rng.normal(0, 2, count)), 0, 30).astype(int)

    risk_score = (
        0.055 * (70 - attendance)
        + 0.09 * (60 - previous_grade)
        + 0.07 * (65 - assignments)
        + 0.18 * absences
        - 0.11 * study_hours
        - 0.45 * support
        + rng.normal(0, 2.2, count)
    )
    # Keep the cohort meaningfully balanced so validation metrics reflect recall as well as accuracy.
    dropout = (risk_score > 0.0).astype(int)

    frame = pd.DataFrame({
        "student_id": [f"STU-{index:04d}" for index in range(1, count + 1)],
        "attendance": np.round(attendance, 1),
        "study_hours": np.round(study_hours, 1),
        "previous_grade": np.round(previous_grade, 1),
        "assignment_completion": np.round(assignments, 1),
        "support_level": support,
        "absences": absences,
        "dropout": dropout,
    })
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DATASET_PATH, index=False)
    print(f"Generated {len(frame)} student records at {DATASET_PATH}")


if __name__ == "__main__":
    main()
