import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
import json
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

EVAL_THRESHOLD = 0.70


def train(
    params_all: dict,
    data_path: str = "data/train_phase1.csv",
    eval_path: str = "data/eval.csv",
) -> float:
    """
    Huan luyen mo hinh va ghi nhan ket qua vao MLflow.
    Supports Bonus 2, 3, 5.
    """

    # Doc du lieu huan luyen va danh gia
    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    # Bonus 5: Canh bao lech lac du lieu
    print("--- Kiem tra phan phoi nhan (Bonus 5) ---")
    label_counts = df_train["target"].value_counts(normalize=True).to_dict()
    label_dist = {str(k): float(v) for k, v in label_counts.items()}
    for label, ratio in label_dist.items():
        print(f"Lop {label}: {ratio:.2%}")
        if ratio < 0.10:
            print(f"!!! CANH BAO: Lop {label} chi chiem {ratio:.2%}, duoi 10% !!!")

    # Tach dac trung (X) va nhan (y)
    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    # Bonus 2: Chon thuat toan
    model_type = params_all.get("model_type", "random_forest")
    params = params_all.get(model_type, {})
    print(f"--- Huan luyen mo hinh: {model_type} ---")

    if model_type == "random_forest":
        model = RandomForestClassifier(**params, random_state=42)
    elif model_type == "gradient_boosting":
        model = GradientBoostingClassifier(**params, random_state=42)
    elif model_type == "logistic_regression":
        model = LogisticRegression(**params, random_state=42)
    else:
        raise ValueError(f"Khong ho tro model_type: {model_type}")

    with mlflow.start_run():
        # Log params
        mlflow.log_param("model_type", model_type)
        mlflow.log_params(params)

        # Huan luyen
        model.fit(X_train, y_train)

        # Danh gia
        preds = model.predict(X_eval)
        acc = accuracy_score(y_eval, preds)
        f1 = f1_score(y_eval, preds, average="weighted")

        # Bonus 3: Tao bao cao hieu suat
        report_text = classification_report(y_eval, preds)
        conf_matrix = confusion_matrix(y_eval, preds)

        os.makedirs("outputs", exist_ok=True)
        with open("outputs/report.txt", "w") as f:
            f.write(f"MODEL TYPE: {model_type}\n")
            f.write(f"ACCURACY: {acc:.4f}\n")
            f.write(f"F1 SCORE: {f1:.4f}\n\n")
            f.write("CLASSIFICATION REPORT:\n")
            f.write(report_text)
            f.write("\nCONFUSION MATRIX:\n")
            f.write(str(conf_matrix))

        # Log metrics vao MLflow
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        mlflow.sklearn.log_model(model, "model")

        # In ket qua ra man hinh
        print(f"Accuracy: {acc:.4f} | F1: {f1:.4f}")

        # Luu metrics ra file (kem theo phan phoi nhan cho Bonus 5)
        with open("outputs/metrics.json", "w") as f:
            json.dump(
                {"accuracy": acc, "f1_score": f1, "label_distribution": label_dist}, f
            )

        # Luu mo hinh
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.pkl")

    return acc


if __name__ == "__main__":
    with open("params.yaml") as f:
        params_all = yaml.safe_load(f)
    train(params_all)
