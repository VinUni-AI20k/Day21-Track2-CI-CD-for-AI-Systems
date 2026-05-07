import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
import json
import joblib
import os
import sys
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
)

EVAL_THRESHOLD = 0.70
os.makedirs("outputs", exist_ok=True)
os.makedirs("models", exist_ok=True)


def get_model(model_type: str, params: dict):
    """Instantiate a model based on model_type."""
    if model_type == "random_forest":
        return RandomForestClassifier(**params, random_state=42)
    elif model_type == "gradient_boosting":
        return GradientBoostingClassifier(**params, random_state=42)
    elif model_type == "logistic_regression":
        return LogisticRegression(**params, random_state=42, max_iter=1000)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def _check_data_drift(y_train) -> dict:
    """
    Bonus 5: Check label distribution for data drift.
    Warns if any class represents less than 10% of total samples.
    """
    total = len(y_train)
    label_dist = {}
    warnings = []
    for label in sorted(y_train.unique()):
        count = int((y_train == label).sum())
        ratio = count / total
        label_dist[int(label)] = {"count": count, "ratio": round(ratio, 4)}
        if ratio < 0.10:
            warnings.append(
                f"WARNING: Class {label} only has {ratio:.1%} of samples (< 10%) - potential data drift!"
            )
    for w in warnings:
        print(w)
    return label_dist


def _save_performance_report(
    y_eval,
    preds,
    output_path: str = "outputs/report.txt",
    metrics: dict = None,
):
    """
    Bonus 3: Save a text-based performance report with confusion matrix,
    precision, recall, and per-class metrics.
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("  MLOps Lab - Model Performance Report")
    report_lines.append("=" * 60)

    if metrics:
        report_lines.append(f"\nAccuracy : {metrics.get('accuracy', 'N/A'):.4f}")
        report_lines.append(f"F1 Score : {metrics.get('f1_score', 'N/A'):.4f}")

    report_lines.append("\n--- Confusion Matrix ---")
    cm = confusion_matrix(y_eval, preds)
    # Header
    report_lines.append("        Pred")
    report_lines.append("True   " + "  ".join(f"{i:>5}" for i in range(cm.shape[1])))
    for i, row in enumerate(cm):
        report_lines.append(
            f"  {i}   " + "  ".join(f"{v:>5}" for v in row)
        )

    report_lines.append("\n--- Per-Class Metrics (Precision / Recall / F1) ---")
    class_names = {0: "thap", 1: "trung_binh", 2: "cao"}
    precision = precision_score(y_eval, preds, average=None, zero_division=0)
    recall = recall_score(y_eval, preds, average=None, zero_division=0)
    f1_per = f1_score(y_eval, preds, average=None, zero_division=0)

    report_lines.append(
        f"{'Class':<12} {'Label':<12} {'Precision':>10} {'Recall':>10} {'F1':>10}"
    )
    report_lines.append("-" * 56)
    for i in range(len(precision)):
        label_str = class_names.get(i, str(i))
        report_lines.append(
            f"{i:<12} {label_str:<12} {precision[i]:>10.4f} {recall[i]:>10.4f} {f1_per[i]:>10.4f}"
        )

    report_lines.append("\n--- Full Classification Report ---")
    report_lines.append(classification_report(y_eval, preds, zero_division=0))

    report_lines.append("=" * 60)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"Performance report saved to {output_path}")


def train(
    params: dict,
    data_path: str = "data/train_phase1.csv",
    eval_path: str = "data/eval.csv",
) -> float:
    """
    Huấn luyện mô hình và ghi nhận kết quả vào MLflow.

    Tham số:
        params     : dict chứa các siêu tham số + model_type
        data_path  : đường dẫn đến file dữ liệu huấn luyện
        eval_path  : đường dẫn đến file dữ liệu đánh giá

    Trả về:
        accuracy (float): độ chính xác trên tập đánh giá
    """

    # Đọc siêu tham số
    model_type = params.pop("model_type", "random_forest")

    # Bonus 5: Kiểm tra data drift trước khi huấn luyện
    df_train_check = pd.read_csv(data_path)
    label_dist = _check_data_drift(df_train_check["target"])

    # Đọc dữ liệu huấn luyện và đánh giá
    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    # Tách đặc trưng và nhãn
    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    # Cấu hình MLflow
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("wine-quality-classification")

    with mlflow.start_run():

        # Ghi nhận siêu tham số
        run_params = {**params, "model_type": model_type}
        mlflow.log_params(run_params)

        # Khởi tạo và huấn luyện mô hình
        model = get_model(model_type, params)
        model.fit(X_train, y_train)

        # Dự đoán và tính các chỉ số
        preds = model.predict(X_eval)
        acc = accuracy_score(y_eval, preds)
        f1 = f1_score(y_eval, preds, average="weighted")
        precision = precision_score(y_eval, preds, average=None, zero_division=0)
        recall = recall_score(y_eval, preds, average=None, zero_division=0)

        # Ghi nhận các chỉ số vào MLflow
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        for i, (p, r) in enumerate(zip(precision, recall)):
            mlflow.log_metric(f"precision_class_{i}", p)
            mlflow.log_metric(f"recall_class_{i}", r)

        # Log label distribution (Bonus 5)
        for label, dist_info in label_dist.items():
            mlflow.log_metric(f"label_dist_class_{label}", dist_info["ratio"])

        # Log mô hình vào MLflow artifact
        mlflow.sklearn.log_model(model, "model")

        # In kết quả
        print(f"Model type : {model_type}")
        print(f"Accuracy   : {acc:.4f}")
        print(f"F1 Score   : {f1:.4f}")

        # Bonus 3: Lưu báo cáo hiệu suất tự động
        metrics_for_report = {"accuracy": acc, "f1_score": f1}
        _save_performance_report(y_eval, preds, metrics=metrics_for_report)

        # Lưu metrics ra file outputs/metrics.json
        # File này được đọc bởi GitHub Actions ở Bước 2
        metrics_data = {
            "accuracy": acc,
            "f1_score": f1,
            "model_type": model_type,
            "label_distribution": label_dist,
            "precision_per_class": [round(float(p), 4) for p in precision],
            "recall_per_class": [round(float(r), 4) for r in recall],
        }
        with open("outputs/metrics.json", "w") as f:
            json.dump(metrics_data, f, indent=2)

        # Lưu mô hình ra file models/model.pkl
        # File này sẽ được upload lên S3 ở Bước 2
        joblib.dump(model, "models/model.pkl")

    # Trả về accuracy để các hàm gọi train() có thể đọc kết quả
    return acc


if __name__ == "__main__":
    # Đọc siêu tham số từ params.yaml và gọi hàm train()
    with open("params.yaml") as f:
        params = yaml.safe_load(f)

    # Nếu muốn thử nhiều thuật toán (Bonus 2), uncomment các dòng bên dưới
    # model_types = ["random_forest", "gradient_boosting", "logistic_regression"]
    # for mt in model_types:
    #     params["model_type"] = mt
    #     train(params)

    acc = train(params)
    print(f"\nFinal accuracy: {acc:.4f}")
    if acc < EVAL_THRESHOLD:
        print(f"WARNING: Accuracy {acc:.4f} is below threshold {EVAL_THRESHOLD}")
