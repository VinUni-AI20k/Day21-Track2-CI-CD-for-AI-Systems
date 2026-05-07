# MLOps Pipeline - Complete Setup Checklist

Use this checklist to track your progress through the setup process.

---

## Phase 1: Local Environment (Completed)

- [x] Python environment set up with virtual environment
- [x] Required packages installed (mlflow, scikit-learn, pandas, dvc, pytest, fastapi, etc.)
- [x] Data files generated (train_phase1.csv, eval.csv, train_phase2.csv)
- [x] DVC initialized with S3 remote
- [x] All code files written (train.py, serve.py, test_train.py, mlops.yml)
- [x] MLflow experiments run
- [x] Code pushed to GitHub
- [x] Local tests passed (5/5 pytest tests)

---

## Phase 2: AWS Setup (Required - User Action)

### 2.1: Create S3 Bucket

- [ ] Go to https://console.aws.amazon.com/s3/
- [ ] Click "Create bucket"
- [ ] Bucket name: `mlops-wine-quality-dung` (or unique name)
- [ ] Region: `us-east-1`
- [ ] Note: Bucket name for later

### 2.2: Create IAM User

- [ ] Go to https://console.aws.amazon.com/iam/
- [ ] Navigate to Users → Add users
- [ ] User name: `mlops-deploy`
- [ ] Access type: Programmatic access
- [ ] Permissions: AmazonS3FullAccess
- [ ] Save Access Key ID: _______________
- [ ] Save Secret Access Key: _______________

### 2.3: Push Data to DVC Remote (After Creating S3 Bucket)

- [ ] Run: `dvc push`

---

## Phase 3: EC2 VM Setup (Required - User Action)

### 3.1: Create EC2 Instance

- [ ] Go to https://console.aws.amazon.com/ec2/
- [ ] Click "Launch instance"
- [ ] Name: `mlops-wine-quality-vm`
- [ ] OS: Ubuntu 22.04 LTS
- [ ] Instance type: t2.small
- [ ] Create new key pair (download .pem file)
- [ ] Security Group:
  - SSH (22) - My IP
  - Custom TCP (8000) - Anywhere
- [ ] Launch instance
- [ ] Note Public IP: _______________

### 3.2: Connect to EC2 and Run Setup

Option A - Automated:
```bash
# Copy setup script to EC2 and run
scp -i "key.pem" setup_vm.sh ubuntu@IP:~/
ssh -i "key.pem" ubuntu@IP
chmod +x setup_vm.sh
./setup_vm.sh
```

Option B - Manual (see VM_SETUP.md):
- SSH into instance
- Install dependencies
- Create directories
- Download serve.py
- Create systemd service
- Enable and start service

### 3.3: Verify VM Setup

- [ ] Test health endpoint: `curl http://VM_IP:8000/health`
- [ ] Test prediction: `curl -X POST http://VM_IP:8000/predict -H "Content-Type: application/json" -d '{"features": [7.0, 0.27, 0.36, 20.7, 0.045, 45.0, 170.0, 1.001, 3.0, 0.45, 8.8, 0]}'`

---

## Phase 4: GitHub Secrets (Required - User Action)

Go to: https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/settings/secrets/actions

### AWS Secrets

| Secret Name | Value |
|------------|-------|
| [ ] AWS_ACCESS_KEY_ID | From IAM user creation |
| [ ] AWS_SECRET_ACCESS_KEY | From IAM user creation |
| [ ] AWS_S3_BUCKET | Bucket name |
| [ ] AWS_REGION | us-east-1 (or your region) |

### VM Secrets

| Secret Name | Value |
|------------|-------|
| [ ] VM_HOST | EC2 Public IP address |
| [ ] VM_USER | ubuntu |
| [ ] VM_SSH_KEY | Private SSH key content |

### MLflow Secret (Optional - for Bonus 1)

| Secret Name | Value |
|------------|-------|
| [ ] MLFLOW_TRACKING_URI | DagsHub or MLflow server URI |

---

## Phase 5: Trigger Pipeline

### 5.1: Push Changes

```bash
git add .
git commit -m "Add AWS and VM setup documentation"
git push origin master
```

### 5.2: Monitor Pipeline

- [ ] Go to: https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/actions
- [ ] Watch for: test → train → eval → deploy
- [ ] Check each job passes

---

## Phase 6: Verification

### Pipeline Verification

- [ ] GitHub Actions - All 4 jobs passed (green)
- [ ] S3 Bucket contains:
  - [ ] `dvc/` folder with data files
  - [ ] `models/latest/model.pkl`
  - [ ] `models/latest/metrics.json`
  - [ ] `models/latest/report.txt`

### API Verification

- [ ] Health endpoint returns: `{"status":"ok"}`
- [ ] Prediction endpoint returns valid response
- [ ] Both endpoints accessible from internet

### Documentation Verification

- [ ] MLflow UI shows experiments with parameters and metrics
- [ ] S3 Console shows uploaded files
- [ ] GitHub Actions logs show successful runs

---

## Bonus Challenges

| Bonus | Description | Points | Status |
|-------|-------------|--------|--------|
| Bonus 1 | MLflow remote tracking with DagsHub | 4 | [ ] |
| Bonus 2 | Multiple algorithm experiments | 4 | [x] |
| Bonus 3 | Auto performance report | 4 | [x] |
| Bonus 4 | Accuracy rollback check | 4 | [x] |
| Bonus 5 | Data distribution warning | 4 | [x] |

---

## Important Notes

1. **Bucket Name Must Be Unique**: S3 bucket names are globally unique. If `mlops-wine-quality-dung` is taken, use a different name and update:
   - `.dvc/config`
   - GitHub Secret `AWS_S3_BUCKET`
   - `serve.py` (S3_BUCKET variable)
   - `scripts/setup_vm.sh`

2. **EC2 Costs**: t2.small is within AWS Free Tier. Monitor usage to avoid charges.

3. **Security**: For production, use IAM roles instead of access keys and restrict security group rules.

4. **Eval Gate**: Pipeline will block deployment if accuracy < 0.70.

---

## Quick Reference

### Repository URL
```
https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems
```

### Key Files
- `.github/workflows/mlops.yml` - CI/CD pipeline
- `src/train.py` - Training script
- `src/serve.py` - FastAPI server
- `tests/test_train.py` - Unit tests
- `params.yaml` - Model hyperparameters

### DVC Remote
```
s3://mlops-wine-quality-dung/dvc
```

### Model Features (12 features in order)
```
fixed_acidity, volatile_acidity, citric_acid, residual_sugar,
chlorides, free_sulfur_dioxide, total_sulfur_dioxide, density,
pH, sulphates, alcohol, wine_type
```

### Prediction Labels
```
0 = "thap" (low quality)
1 = "trung_binh" (medium quality)
2 = "cao" (high quality)
```
