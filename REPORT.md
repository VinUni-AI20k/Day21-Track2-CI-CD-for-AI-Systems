# MLOps Lab Report - Day 21

**Họ và tên:** Phạm Hoàng Long
**Mã số học viên:** 2A202600261
**Repo URL:** https://github.com/GolDDragon1702/Day21-Track2-CI-CD-for-AI-Systems.git

## 1. Kết quả thực nghiệm (Bước 1)
- **Bộ siêu tham số tốt nhất:** 
  - `n_estimators`: 500
  - `max_depth`: null
  - `min_samples_split`: 5
- **Lý do chọn:** Qua quan sát trên MLflow UI, bộ thông số này cho độ chính xác (Accuracy) cao nhất (~0.82) và chỉ số F1-score ổn định nhất so với các lần chạy với `n_estimators` thấp hơn.

## 2. Khó khăn gặp phải và Cách giải quyết
Trong quá trình thực hiện Bước 2 và 3, tôi đã gặp một số vấn đề về hạ tầng và cấu hình CI/CD:

1. **Vấn đề kết nối SSH và lỗi `i/o timeout`:**
   - *Nguyên nhân:* Cổng 22 trên AWS Security Group chưa được mở và mất file `.pem` gốc.
   - *Giải quyết:* Đã mở cổng 22 (Inbound Rule) cho phép `0.0.0.0/0`. Tự tạo cặp SSH key mới, dùng EC2 Instance Connect để thêm Public Key vào `authorized_keys` trên VM và cập nhật Private Key vào GitHub Secrets.

2. **Lỗi `ModuleNotFoundError` và `NoCredentialsError` trên VM:**
   - *Nguyên nhân:* VM Amazon Linux chưa cài đặt `pip3`, thiếu thư viện `fastapi`, `boto3` và chưa có quyền truy cập S3.
   - *Giải quyết:* Cài đặt `python3-pip`, cài các thư viện cần thiết qua `pip3`. Gán IAM Role `AmazonS3ReadOnlyAccess` cho Instance EC2 để service có thể tải model từ S3 thành công.

3. **Cấu hình Systemd Service:**
   - *Nguyên nhân:* Chưa tạo file unit service nên lệnh `restart` trong pipeline bị lỗi.
   - *Giải quyết:* Đã tạo file `/etc/systemd/system/mlops-serve.service` với các biến môi trường `S3_BUCKET` tương ứng.

## 3. Các Bonus đã thực hiện
Đã hoàn thành 4 bonus tasks (Bonus 2, 3, 4, 5):

1. **Bonus 2 - Thí Nghiệm Với Nhiều Thuật Toán:**
   - Mở rộng `src/train.py` để hỗ trợ 3 thuật toán: RandomForest, GradientBoosting, LogisticRegression.
   - Thêm tham số `model_type` vào `params.yaml` để chọn thuật toán.
   - Có thể chạy thí nghiệm với các thuật toán khác nhau và so sánh trên MLflow UI.

2. **Bonus 3 - Báo Cáo Hiệu Suất Tự Động:**
   - Tạo file `outputs/report.txt` sau mỗi lần huấn luyện với đầy đủ thông tin:
     - Classification report (precision, recall, f1-score cho từng lớp)
     - Confusion matrix dạng văn bản
   - Upload artifact `report.txt` lên GitHub Actions để lưu trữ và xem lại.

3. **Bonus 4 - Hoàn Trả Về Phiên Bản Trước (Rollback):**
   - Thêm job `rollback_check` vào pipeline CI/CD.
   - Trước khi deploy, tải `metrics.json` của lần chạy trước từ S3.
   - So sánh accuracy mới với accuracy cũ, chỉ deploy khi accuracy mới >= accuracy cũ.
   - Upload metrics mới lên S3 sau khi deploy thành công để so sánh với lần sau.
   - Ghi log kết quả so sánh rõ ràng vào pipeline.

4. **Bonus 5 - Cảnh Báo Lệch Lạc Dữ Liệu:**
   - Thêm bước kiểm tra phân phối nhãn trong tập huấn luyện.
   - Tính tỷ lệ mẫu của từng lớp (0, 1, 2).
   - Cảnh báo rõ ràng nếu bất kỳ lớp nào chiếm ít hơn 10% tổng mẫu.
   - Ghi tỷ lệ phân phối nhãn vào `outputs/metrics.json` cùng với accuracy và f1_score.

## 4. Kết luận
Pipeline CI/CD đã hoạt động hoàn chỉnh với đầy đủ các tính năng bonus. Mỗi khi push dữ liệu mới qua DVC, hệ thống tự động trigger quá trình Train -> Eval -> Rollback Check -> Deploy, đảm bảo mô hình trên server luôn là phiên bản tốt nhất và an toàn.
