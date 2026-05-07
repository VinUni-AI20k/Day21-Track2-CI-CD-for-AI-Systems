# All Bugs & Issues — Day 21 CI/CD Pipeline

---

## Vấn đề 1: Tất cả pipeline jobs (1–10) đều thất bại, chỉ job gần nhất thành công

**Mô tả:** Các pipeline run trước đó đều fail, chỉ run #11 (sau khi reset) mới pass.

**Nguyên nhân gốc:** Nhiều vấn đề lẻ tẻ tích lũy qua các lần fix:
- `.dvc/config` chưa tồn tại trong repo
- GitHub Secrets chưa đầy đủ (`VM_SSH_KEY`, `MLFLOW_TRACKING_URI`, credentials AWS)
- YAML syntax error trong `mlops.yml` (SSH action không tương thích)
- `dvc pull` chỉ kéo 1 file DVC thay vì 3 file

**Cách giải quyết:** Reset pipeline, commit từng fix nhỏ, re-run cho đến khi pass. Cuối cùng Pipeline #11 pass toàn bộ 4 jobs.

---

## Vấn đề 2: Eval job fail — accuracy 0.68 < ngưỡng 0.70

**Mô tả:** Eval job trên CI bị fail với thông báo accuracy không đạt ngưỡng.

**Nguyên nhân gốc:**
1. `dvc pull` trong CI chỉ kéo `train_phase1.csv.dvc`, thiếu `train_phase2.csv.dvc` → model chỉ train trên 2998 mẫu thay vì 5996 mẫu
2. File `metrics.json` trên S3 bị ghi đè bởi các run cũ có accuracy thấp

**Cách giải quyết:** Cập nhật lệnh `dvc pull` trong `mlops.yml`:
```yaml
dvc pull data/train_phase1.csv.dvc data/eval.csv.dvc data/train_phase2.csv.dvc
```
Sửa logic eval để đọc `metrics.json` từ S3 sau khi train job upload.

---

## Vấn đề 3: SSH key lỗi trong Deploy job

**Mô tả:** Deploy job thất bại khi SSH vào VM để restart service.

**Nguyên nhân gốc:** GitHub Secret `VM_SSH_KEY` chưa được cấu hình đúng (thiếu private key).

**Cách giải quyết:**
1. Copy nội dung file `mlops-key` (private key)
2. Paste vào GitHub repo → Settings → Secrets and variables → Actions → New secret
3. Đặt tên: `VM_SSH_KEY`, paste nội dung key
4. Re-run pipeline

---

## Vấn đề 4: YAML syntax error trong GitHub Actions

**Mô tả:** GitHub Actions báo lỗi YAML syntax khi chạy deploy job.

**Nguyên nhân gốc:** GitHub Action `appleboy/ssh-action` không tương thích với cấu hình hiện tại. Block `script:` trong YAML gây lỗi.

**Cách giải quyết:** Thay thế SSH action bằng lệnh SSH trực tiếp trong step `run:`:
```yaml
- name: Restart mlops-serve on VM
  run: |
    echo "$VM_SSH_KEY" > /tmp/deploy_key && chmod 600 /tmp/deploy_key
    ssh -o StrictHostKeyChecking=no -i /tmp/deploy_key "$VM_USER@$VM_HOST" \
      "sudo systemctl restart mlops-serve && sleep 10 && curl -sf http://localhost:8000/health"
```

---

## Vấn đề 5: Thiếu file .dvc/config trong repo

**Mô tả:** `dvc pull` trong CI thất bại vì không tìm thấy remote configuration.

**Nguyên nhân gốc:** File `.dvc/config` chưa được commit lên repo.

**Cách giải quyết:** Tạo file `.dvc/config` với nội dung:
```ini
[core]
    remote = myremote
[remote "myremote"]
    url = s3://mlops-wine-quality-dung/dvc
    region = ap-southeast-2
```
Commit và push lên GitHub.

---

## Vấn đề 6: MLflow trên DagsHub chỉ có 1 thí nghiệm

**Mô tả:** Sau khi hoàn thành Bonus 1 (DagsHub MLflow), MLflow UI chỉ hiển thị 1 thí nghiệm, không đạt yêu cầu ≥ 3 thí nghiệm của rubric.

**Nguyên nhân gốc:** `train.py` chỉ chạy 1 lần với RandomForest (từ params.yaml), các thuật toán khác còn comment trong code.

**Cách giải quyết:** Sửa `train.py` để tự động chạy 3 experiments:
```python
experiments = [
    {"name": "gradient_boosting", "model_type": "gradient_boosting",
     "params": {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1}},
    {"name": "logistic_regression", "model_type": "logistic_regression",
     "params": {"C": 1.0, "max_iter": 1000}},
    # RandomForest chạy cuối — kết quả dùng cho eval gate
    {"name": "random_forest_best", "model_type": "random_forest",
     "params": dict(params)},
]
for exp in experiments:
    acc = train(p)
```
**Lưu ý quan trọng:** RandomForest phải chạy CUỐI cùng vì `metrics.json` được ghi đè sau mỗi experiment. Accuracy cao nhất (RF: 0.748) cần ở cuối để eval gate pass.

---

## Vấn đề 7: Lệnh curl không hoạt động trên Windows PowerShell

**Mô tả:** Lệnh `curl -sf http://...` báo lỗi trên PowerShell.

**Nguyên nhân gốc:** PowerShell dùng `Invoke-WebRequest` thay vì curl thật. Cờ `-sf` không tương thích.

**Cách giải quyết:** Dùng Python thay thế:
```python
python -c "import requests; print(requests.post('http://13.239.11.6:8000/predict', json={'features':[7.4,0.7,0.0,1.9,0.076,11.0,34.0,0.9978,3.51,0.56,9.4,0]}).text)"
```
Hoặc dùng `curl.exe` thay vì `curl`.

---

## Vấn đề 8: AWS EC2 tốn phí khi chạy liên tục

**Mô tả:** EC2 instance t3.micro đang chạy 24/7, tốn chi phí AWS.

**Nguyên nhân gốc:** Instance được start để phục vụ lab và chưa được tắt sau khi nộp bài.

**Cách giải quyết:**
- **Tắt tạm (Stop):** Giữ dữ liệu, sau bật lại được
  ```bash
  aws ec2 stop-instances --instance-ids i-042eeaac684f7d403
  ```
- **Xóa vĩnh viễn (Terminate):** Không tốn phí nhưng mất instance
  ```bash
  aws ec2 terminate-instances --instance-ids i-042eeaac684f7d403
  ```
- **Giữ S3:** Chi phí rất thấp (~$0.02/tháng), nên giữ vì chứa model và data cần cho bài nộp.

---

## Tóm tắt theo thứ tự thời gian

| # | Vấn đề | Thời điểm | Trạng thái |
|---|---|---|---|
| 1 | Pipeline jobs 1–10 fail | Đầu giờ | ✅ Đã fix |
| 2 | Eval accuracy 0.68 < 0.70 | Đầu giờ | ✅ Đã fix |
| 3 | SSH key lỗi | Pipeline #1–5 | ✅ Đã fix |
| 4 | YAML syntax error | Pipeline #3 | ✅ Đã fix |
| 5 | Thiếu .dvc/config | Pipeline #1–4 | ✅ Đã fix |
| 6 | DagsHub MLflow = 1 experiment | Sau khi setup Bonus 1 | ✅ Đã fix |
| 7 | curl lỗi trên PowerShell | Test VM API | ✅ Đã fix |
| 8 | EC2 tốn phí | Sau khi nộp bài | ⏳ Chờ user tắt |
