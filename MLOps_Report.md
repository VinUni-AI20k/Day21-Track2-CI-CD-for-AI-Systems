# MLOps Lab Report — Day 21: CI/CD for AI Systems

**Họ và tên:** Pham Quoc Dung  
**MSSV:** 2A202600490  
**Repo:** https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems

---

## 1. Bộ Siêu Tham Số Đã Chọn

Sau khi thử nghiệm với 3 thuật toán (RandomForest, GradientBoosting, LogisticRegression) và nhiều bộ tham số khác nhau trên MLflow (DagsHub remote tracking), bộ siêu tham số tốt nhất là:

| Tham số | Giá trị |
|---|---|
| `model_type` | `random_forest` |
| `n_estimators` | 500 |
| `max_depth` | `null` (không giới hạn) |
| `min_samples_split` | 2 |
| `min_samples_leaf` | 1 |
| `class_weight` | `balanced` (tự động) |

**Lý do chọn RandomForest:**
- RandomForest cho accuracy cao nhất (0.748) trên tập eval so với GradientBoosting và LogisticRegression.
- `n_estimators=500` đủ lớn để giảm variance mà không tăng đáng kể thời gian train.
- `class_weight='balanced'` tự động cân bằng trọng số các lớp, giúp cải thiện recall cho lớp thiểu số (class 2 - rượu chất lượng cao).
- Dữ liệu huấn luyện kết hợp từ phase1 (2998 mẫu) và phase2 (2998 mẫu), tổng 5996 mẫu.

**Kết quả đánh giá trên tập eval (500 mẫu):**
- Accuracy: **0.7480**
- F1 Score (weighted): **0.7477**

---

## 2. Khó Khăn và Cách Giải Quyết

### Khó khăn 1: Pipeline CI/CD liên tục thất bại ở job Eval
- **Nguyên nhân:** File `metrics.json` trên S3 bị ghi đè bởi các run trước đó, khiến eval gate so sánh sai. Ngoài ra, dvc pull chỉ tải `train_phase1.csv.dvc`, thiếu `train_phase2.csv.dvc`, dẫn đến model chỉ train trên 2998 mẫu thay vì 5996 mẫu, accuracy chỉ đạt 0.68.
- **Cách giải quyết:** Cập nhật `dvc pull` trong mlops.yml bao gồm cả 3 file `.dvc`. Tối ưu siêu tham số RandomForest với `n_estimators=500`. Sửa logic eval để đọc `metrics.json` trực tiếp từ S3.

### Khó khăn 2: Deploy job thất bại do SSH key
- **Nguyên nhân:** GitHub Secret `VM_SSH_KEY` chưa được cấu hình đúng (thiếu private key).
- **Cách giải quyết:** Hướng dẫn cấu hình SSH key bằng cách copy nội dung file `mlops-key` vào GitHub Secret `VM_SSH_KEY`.

### Khó khăn 3: YAML syntax error trong GitHub Actions
- **Nguyên nhân:** GitHub Action `appleboy/ssh-action` không tương thích với cấu hình hiện tại, và `script:` block bị lỗi syntax.
- **Cách giải quyết:** Thay thế SSH action bằng lệnh SSH trực tiếp trong step `run:`.

### Khó khăn 4: Thiếu .dvc/config
- **Nguyên nhân:** File `.dvc/config` không tồn tại trong repo, khiến `dvc pull` trong CI thất bại.
- **Cách giải quyết:** Tạo file `.dvc/config` với S3 remote đã cấu hình (`s3://mlops-wine-quality-dung/dvc`, region `ap-southeast-2`).

---

## 3. Kiến Trúc Hoàn Chỉnh

```
[Máy tính cá nhân]
      |
      |  git push
      v
[GitHub: clean-main branch]
      |
      |  GitHub Actions (automatic trigger)
      v
[Test → Train (DVC pull, train RF) → Eval (acc >= 0.70) → Deploy (SSH to EC2)]
      |                                    |                    |
      |  MLflow logging (DagsHub)          |  Upload model     |  Restart service
      v                                    v                    v
[DagsHub MLflow UI]           [AWS S3: mlops-wine-quality-dung]   [EC2: mlops-serve]
  (remote tracking)             - models/latest/model.pkl            - FastAPI
                                - metrics.json                       - Port 8000
```

## 4. Bonus Points

| Bonus | Mô tả | Điểm |
|---|---|---|
| Bonus 1 | MLflow remote tracking qua DagsHub | 4 |
| Bonus 2 | Thí nghiệm với 3 thuật toán (RF, GB, LR) | 4 |
| Bonus 3 | Báo cáo hiệu suất tự động (confusion matrix, precision/recall per class) | 4 |
| Bonus 4 | Rollback check - so sánh accuracy model mới vs cũ | 4 |
| Bonus 5 | Data drift warning - cảnh báo class < 10% samples | 4 |
