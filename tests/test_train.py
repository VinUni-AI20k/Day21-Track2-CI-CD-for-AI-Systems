import os
import json
import numpy as np
import pandas as pd
from src.train import train


FEATURE_NAMES = [
    "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density",
    "pH", "sulphates", "alcohol", "wine_type",
]


def _make_temp_data(tmp_path):
    """
    Tao dataset nho voi cung schema Wine Quality de su dung trong test.

    pytest cung cap `tmp_path` la mot thu muc tam thoi, tu dong xoa sau khi test ket thuc.
    Ham nay dung du lieu ngau nhien nen khong can ket noi S3 hay tai file CSV thuc.
    """
    rng = np.random.default_rng(0)
    n = 200

    # Tao mang X co kich thuoc (n, len(FEATURE_NAMES)) voi gia tri [0, 1)
    X = rng.random((n, len(FEATURE_NAMES)))

    # Tao mang y gom n phan tu nguyen ngau nhien trong [0, 3)
    y = rng.integers(0, 3, size=n)

    # Xay dung DataFrame, them cot "target"
    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["target"] = y

    # Luu 160 dong dau lam tap huan luyen, 40 dong cuoi lam tap danh gia
    train_path = str(tmp_path / "train.csv")
    eval_path = str(tmp_path / "eval.csv")
    df.iloc[:160].to_csv(train_path, index=False)
    df.iloc[160:].to_csv(eval_path, index=False)

    # Tra ve (train_path, eval_path)
    return train_path, eval_path


def test_train_returns_float(tmp_path):
    """Kiem tra ham train() tra ve mot so thuc nam trong [0.0, 1.0]."""
    train_path, eval_path = _make_temp_data(tmp_path)

    # Goi ham train() voi sieu tham so nho (n_estimators=10, max_depth=3)
    # va cac duong dan file vua tao
    acc = train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    # Kiem tra ket qua
    assert isinstance(acc, float), f"Expected float, got {type(acc)}"
    assert 0.0 <= acc <= 1.0, f"Accuracy {acc} out of [0, 1] range"


def test_metrics_file_created(tmp_path):
    """Kiem tra file outputs/metrics.json duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    # Kiem tra file ton tai va noi dung dung dinh dang
    assert os.path.exists("outputs/metrics.json"), "outputs/metrics.json not found"
    with open("outputs/metrics.json") as f:
        metrics = json.load(f)
    assert "accuracy" in metrics, "metrics.json missing 'accuracy'"
    assert "f1_score" in metrics, "metrics.json missing 'f1_score'"
    assert isinstance(metrics["accuracy"], (int, float))
    assert isinstance(metrics["f1_score"], (int, float))


def test_model_file_created(tmp_path):
    """Kiem tra file models/model.pkl duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    # Kiem tra file model ton tai
    assert os.path.exists("models/model.pkl"), "models/model.pkl not found"


def test_train_with_gradient_boosting(tmp_path):
    """Kiem tra train hoat dong voi gradient_boosting (Bonus 2)."""
    train_path, eval_path = _make_temp_data(tmp_path)
    acc = train(
        {"n_estimators": 5, "max_depth": 3, "learning_rate": 0.1},
        data_path=train_path,
        eval_path=eval_path,
    )
    assert isinstance(acc, float)
    assert 0.0 <= acc <= 1.0


def test_train_with_logistic_regression(tmp_path):
    """Kiem tra train hoat dong voi logistic_regression (Bonus 2)."""
    train_path, eval_path = _make_temp_data(tmp_path)
    acc = train(
        {"C": 1.0, "max_iter": 200},
        data_path=train_path,
        eval_path=eval_path,
    )
    assert isinstance(acc, float)
    assert 0.0 <= acc <= 1.0
