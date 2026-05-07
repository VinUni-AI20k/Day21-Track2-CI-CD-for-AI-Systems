# Hướng Dẫn Chạy Các Bonus Tasks

## Tổng quan
Đã hoàn thành 4 bonus tasks (Bonus 2, 3, 4, 5). Dưới đây là hướng dẫn chi tiết cách chạy và kiểm tra từng bonus.

---

## Bonus 2: Thí Nghiệm Với Nhiều Thuật Toán

### Cách chạy

#### 1. Chạy cục bộ (local)

**Bước 1:** Chuyển đổi thuật toán trong `params.yaml`

```bash
# Mở file params.yaml
nano params.yaml
```

Thay đổi giá trị `model_type`:
- `random_forest` (mặc định)
- `gradient_boosting`
- `logistic_regression`

Ví dụ để chạy Gradient Boosting:
```yaml
model_type: "gradient_boosting"
random_forest:
  n_estimators: 500
  max_depth: null
  min_samples_split: 5
gradient_boosting:
  n_estimators: 100
  learning_rate: 0.1
  max_depth: 3
logistic_regression:
  C: 1.0
  max_iter: 1000
```

**Bước 2:** Chạy huấn luyện
```bash
python src/train.py
```

**Bước 3:** Xem kết quả trên MLflow UI
```bash
mlflow ui
```
Mở trình duyệt tại `http://localhost:5000` và so sánh các runs với các thuật toán khác nhau.

#### 2. Chạy trên GitHub Actions

**Bước 1:** Commit thay đổi `params.yaml`
```bash
git add params.yaml
git commit -m "Test gradient boosting algorithm"
git push
```

**Bước 2:** GitHub Actions sẽ tự động chạy với thuật toán mới
- Vào tab "Actions" trên GitHub
- Chọn workflow run mới nhất
- Xem job "Train" để thấy thuật toán đang chạy

---

## Bonus 3: Báo Cáo Hiệu Suất Tự Động

### Cách chạy

#### 1. Chạy cục bộ (local)

**Bước 1:** Chạy huấn luyện bình thường
```bash
python src/train.py
```

**Bước 2:** Xem báo cáo được tạo
```bash
cat outputs/report.txt
```

File `report.txt` sẽ chứa:
- Model type
- Accuracy và F1 score
- Classification report (precision, recall, f1-score cho từng lớp)
- Confusion matrix

#### 2. Chạy trên GitHub Actions

**Bước 1:** Push code lên GitHub
```bash
git add .
git commit -m "Run training with performance report"
git push
```

**Bước 2:** Tải xuống artifact từ GitHub Actions
- Vào tab "Actions" trên GitHub
- Chọn workflow run
- Cuộn xuống phần "Artifacts"
- Tải xuống artifact có tên `report`
- Giải nén và mở file `report.txt`

---

## Bonus 4: Hoàn Trả Về Phiên Bản Trước (Rollback)

### Cách chạy

#### Cơ chế hoạt động
- Job `rollback_check` chạy sau job `eval`
- Tải `metrics.json` cũ từ S3 (nếu có)
- So sánh accuracy mới với accuracy cũ
- Chỉ deploy khi accuracy mới >= accuracy cũ
- Upload metrics mới lên S3 sau khi deploy thành công

#### Chạy thử nghiệm rollback

**Bước 1:** Chạy lần đầu tiên (baseline)
```bash
# Đảm bảo params.yaml có model_type = "random_forest"
git add params.yaml
git commit -m "Initial deploy with random forest"
git push
```
- Pipeline sẽ chạy và deploy thành công
- Metrics sẽ được upload lên S3 tại `metrics/metrics.json`

**Bước 2:** Chạy với model tốt hơn (nên deploy)
```bash
# Thay đổi tham số để cải thiện accuracy
# Ví dụ: tăng n_estimators
nano params.yaml
# Thay đổi: n_estimators: 1000

git add params.yaml
git commit -m "Improve model with more estimators"
git push
```
- Pipeline sẽ so sánh accuracy mới với cũ
- Nếu accuracy mới >= cũ, deploy sẽ tiếp tục
- Xem log job "Rollback Check" để thấy kết quả so sánh

**Bước 3:** Chạy với model kém hơn (không nên deploy)
```bash
# Thay đổi tham số để giảm accuracy
# Ví dụ: giảm n_estimators
nano params.yaml
# Thay đổi: n_estimators: 10

git add params.yaml
git commit -m "Test rollback with poor model"
git push
```
- Pipeline sẽ so sánh accuracy mới với cũ
- Nếu accuracy mới < cũ, deploy sẽ bị hủy
- Xem log job "Rollback Check" để thấy thông báo "HUY DEPLOY de rollback"

#### Xem log so sánh accuracy

Vào GitHub Actions → Chọn workflow run → Chọn job "Rollback Check" → Xem log:
```
Accuracy cu: 0.8200
Accuracy moi: 0.8300
>>> PASS: Accuracy moi (0.8300) >= Accuracy cu (0.8200). Cho phep deploy.
```

Hoặc:
```
Accuracy cu: 0.8200
Accuracy moi: 0.7500
>>> FAIL: Accuracy moi (0.7500) < Accuracy cu (0.8200). HUY DEPLOY de rollback.
```

---

## Bonus 5: Cảnh Báo Lệch Lạc Dữ Liệu

### Cách chạy

#### 1. Chạy cục bộ (local)

**Bước 1:** Chạy huấn luyện bình thường
```bash
python src/train.py
```

**Bước 2:** Xem cảnh báo trong terminal
```
--- Kiem tra phan phoi nhan (Bonus 5) ---
Lop 0: 35.00%
Lop 1: 45.00%
Lop 2: 20.00%
```

Nếu bất kỳ lớp nào < 10%, sẽ hiện cảnh báo:
```
!!! CANH BAO: Lop 2 chi chiem 5.00%, duoi 10% !!!
```

**Bước 3:** Xem phân phối trong metrics.json
```bash
cat outputs/metrics.json
```
Kết quả:
```json
{
  "accuracy": 0.82,
  "f1_score": 0.81,
  "label_distribution": {
    "0": 0.35,
    "1": 0.45,
    "2": 0.20
  }
}
```

#### 2. Chạy trên GitHub Actions

**Bước 1:** Push code lên GitHub
```bash
git add .
git commit -m "Run training with data distribution check"
git push
```

**Bước 2:** Xem log job "Train" trên GitHub Actions
- Vào tab "Actions"
- Chọn workflow run
- Chọn job "Train"
- Xem log để thấy phân phối nhãn và cảnh báo (nếu có)

#### Tạo dữ liệu lệch lạc để test

Nếu muốn test cảnh báo, có thể tạo tập dữ liệu không cân bằng:

```bash
# Tạo tập dữ liệu mới với phân phối lệch
python - <<'EOF'
import pandas as pd
import numpy as np

# Đọc dữ liệu gốc
df = pd.read_csv("data/train_phase1.csv")

# Tạo phân phối lệch (lớp 0 chiếm 80%, lớp 1 chiếm 15%, lớp 2 chiếm 5%)
df_0 = df[df["target"] == 0].sample(n=2400, random_state=42)
df_1 = df[df["target"] == 1].sample(n=450, random_state=42)
df_2 = df[df["target"] == 2].sample(n=148, random_state=42)

df_imbalanced = pd.concat([df_0, df_1, df_2]).sample(frac=1, random_state=42)
df_imbalanced.to_csv("data/train_phase1.csv", index=False)
print("Đã tạo dữ liệu lệch lạc")
EOF

# Commit và push
git add data/train_phase1.csv data/train_phase1.csv.dvc
dvc commit data/train_phase1.csv.dvc
git commit -m "Test with imbalanced data"
git push
```

Pipeline sẽ hiện cảnh báo trong log:
```
--- Kiem tra phan phoi nhan (Bonus 5) ---
Lop 0: 80.00%
Lop 1: 15.00%
Lop 2: 5.00%
!!! CANH BAO: Lop 2 chi chiem 5.00%, duoi 10% !!!
```

---

## Chạy Tất Cả Bonus Cùng Lúc

Để chạy tất cả bonus trong một pipeline:

```bash
# 1. Đảm bảo params.yaml có model_type = "random_forest"
nano params.yaml

# 2. Commit tất cả thay đổi
git add .
git commit -m "Run pipeline with all bonuses enabled"
git push
```

GitHub Actions sẽ tự động:
1. Chạy unit tests
2. Pull data từ S3
3. Huấn luyện model với thuật toán đã chọn (Bonus 2)
4. Kiểm tra phân phối dữ liệu (Bonus 5)
5. Tạo báo cáo hiệu suất (Bonus 3)
6. Upload artifacts (metrics.json và report.txt)
7. So sánh với model cũ (Bonus 4)
8. Deploy nếu đạt điều kiện

---

## Kiểm Tra Kết Quả

### Local
- MLflow UI: `http://localhost:5000`
- Report file: `outputs/report.txt`
- Metrics file: `outputs/metrics.json`

### GitHub Actions
- Vào repo GitHub → Tab "Actions"
- Chọn workflow run gần nhất
- Xem log từng job
- Tải artifacts từ phần "Artifacts" ở cuối trang

### Cloud Storage (S3)
```bash
# Xem metrics đã upload
aws s3 ls s3://<YOUR_BUCKET>/metrics/

# Tải metrics cũ
aws s3 cp s3://<YOUR_BUCKET>/metrics/metrics.json /tmp/old_metrics.json
```
