# AWS Setup Guide for MLOps Pipeline

## Overview

This guide walks you through setting up AWS resources needed for the MLOps CI/CD pipeline. Since you're on Windows without AWS CLI, we'll use the AWS Management Console (web browser).

---

## Step 1: Create S3 Bucket

The S3 bucket stores:
- Training data (via DVC)
- Trained model files (`models/model.pkl`)
- Performance reports

### Actions:

1. Go to AWS Console: https://console.aws.amazon.com/s3/
2. Click **"Create bucket"**
3. Configure:
   - **Bucket name**: `mlops-wine-quality-dung` (must be globally unique, add numbers if taken)
   - **AWS Region**: `us-east-1` (or your preferred region)
   - **Object Ownership**: `ACLs disabled` (recommended)
   - **Block Public Access**: Keep checked (default)
4. Click **"Create bucket"**
5. **Note**: Copy the bucket name and region - you'll need these for GitHub Secrets

### Verify:
After creation, you should see your bucket in the S3 console at:
`https://s3.console.aws.amazon.com/s3/buckets/mlops-wine-quality-dung`

---

## Step 2: Create IAM User

The IAM user provides programmatic access (Access Key + Secret Key) for:
- GitHub Actions to upload model files to S3
- DVC to pull/push data

### Actions:

1. Go to IAM Console: https://console.aws.amazon.com/iam/
2. Navigate to **Users** → **Add users**
3. Configure:
   - **User name**: `mlops-deploy`
   - **Access type**: Check ✅ **Access key - Programmatic access**
4. Click **Next: Permissions**
5. Select **"Attach existing policies directly"**
6. Search and select: **AmazonS3FullAccess** (or create a custom policy for least privilege)
7. Click **Next: Tags** (optional, can skip)
8. Click **Next: Review**
9. Click **"Create user"**

### IMPORTANT - Save These Values Immediately:

After creation, you'll see:
- **Access key ID**: `AKIA...` - Save this!
- **Secret access key**: `...` - Save this!

**You cannot retrieve the Secret Access Key again. If you lose it, you must create a new access key.**

Store them securely (password manager, etc.)

---

## Step 3: Update DVC Remote (Optional - Already Configured)

The DVC remote is already configured in `.dvc/config`:
```
[core]
    remote = myremote
[remote "myremote"]
    url = s3://mlops-wine-quality-dung/dvc
```

If you created a bucket with a different name, update the remote:

```bash
dvc remote modify myremote url s3://YOUR-BUCKET-NAME/dvc
dvc remote add myremote s3://YOUR-BUCKET-NAME/dvc
```

---

## Step 4: Configure GitHub Secrets

Go to: https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/settings/secrets/actions

Click **"New repository secret"** and add:

| Secret Name | Value |
|------------|-------|
| `AWS_ACCESS_KEY_ID` | Your IAM user Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | Your IAM user Secret Access Key |
| `AWS_S3_BUCKET` | Your bucket name (e.g., `mlops-wine-quality-dung`) |
| `AWS_REGION` | Your bucket region (e.g., `us-east-1`) |

---

## Step 5: Test S3 Access (Optional)

To verify your credentials work:

1. Go to S3 Console
2. Navigate to your bucket
3. Try to upload a test file manually

If you can upload manually but DVC fails, check:
- IAM permissions are correct
- Bucket is in the same region as specified

---

## Troubleshooting

### Access Denied Errors

1. **Verify IAM Policy**: Ensure `AmazonS3FullAccess` or appropriate S3 permissions are attached
2. **Check Bucket Region**: Make sure the region in GitHub Secret matches the bucket's region
3. **Verify Access Key**: Double-check the Access Key ID and Secret Access Key are correct

### DVC Push/Pull Fails

Ensure AWS credentials are properly set:
- Check GitHub Secrets are configured correctly
- Verify the secret names match exactly (case-sensitive)

### Bucket Name Already Exists

S3 bucket names must be globally unique. Try:
- Add your name/number: `mlops-wine-quality-dung-123`
- Add region suffix: `mlops-wine-quality-dung-us-east-1`

---

## Next Steps

After completing AWS setup:
1. Continue to [VM Setup Guide](./VM_SETUP.md)
2. Add VM-related GitHub Secrets (VM_HOST, VM_USER, VM_SSH_KEY)
3. Push changes to GitHub to trigger the pipeline
