# Knowledge Base Embedding Lambda - Deployment Guide

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. Python 3.9 or later
4. Knowledge base files uploaded to S3

## Step 1: Prepare Dependencies

The Lambda function requires several Python packages that need to be packaged as a Lambda layer or included in the deployment package.

### Option A: Create Lambda Layer (Recommended)

```bash
# Create a directory for the layer
mkdir -p lambda-layer/python

# Install dependencies
pip install -r requirements.txt -t lambda-layer/python/

# Create layer zip
cd lambda-layer
zip -r ../kb-embedding-layer.zip .
cd ..

# Upload layer to AWS
aws lambda publish-layer-version \
  --layer-name kb-embedding-dependencies \
  --description "Dependencies for KB Embedding Lambda" \
  --zip-file fileb://kb-embedding-layer.zip \
  --compatible-runtimes python3.9 python3.10 python3.11
```

### Option B: Include in Deployment Package

```bash
# Install dependencies locally
pip install -r requirements.txt -t .

# Create deployment package
zip -r kb-embedding-function.zip kb_embedding.py faiss_utils.py
```

## Step 2: Create IAM Role

Create an IAM role with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-KNOWLEDGE-BASE-BUCKET",
        "arn:aws:s3:::YOUR-KNOWLEDGE-BASE-BUCKET/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-KNOWLEDGE-BASE-BUCKET/faiss-indices/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/YOUR-EMBEDDINGS-TABLE"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v1"
    }
  ]
}
```

## Step 3: Create Lambda Function

```bash
# Create the Lambda function
aws lambda create-function \
  --function-name KnowledgeBaseEmbeddingFunction \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR-ACCOUNT-ID:role/YOUR-LAMBDA-ROLE \
  --handler kb_embedding.handler \
  --zip-file fileb://kb-embedding-function.zip \
  --timeout 900 \
  --memory-size 3008 \
  --environment Variables="{
    KNOWLEDGE_BASE_BUCKET=your-bucket-name,
    EMBEDDINGS_TABLE=your-table-name,
    AWS_REGION=us-east-1
  }"
```

### Important Configuration Notes

- **Timeout**: Set to 900 seconds (15 minutes) to allow processing of all knowledge base files
- **Memory**: Set to 3008 MB for FAISS operations and large text processing
- **Runtime**: Python 3.11 recommended for best performance

## Step 4: Attach Lambda Layer (if using Option A)

```bash
aws lambda update-function-configuration \
  --function-name KnowledgeBaseEmbeddingFunction \
  --layers arn:aws:lambda:REGION:ACCOUNT-ID:layer:kb-embedding-dependencies:VERSION
```

## Step 5: Upload Knowledge Base Files to S3

Ensure your knowledge base files are in the correct location:

```bash
aws s3 cp knowledge-base/diabetes.txt s3://YOUR-BUCKET/knowledge-base/diabetes.txt
aws s3 cp knowledge-base/blood-pressure.txt s3://YOUR-BUCKET/knowledge-base/blood-pressure.txt
aws s3 cp knowledge-base/cholesterol.txt s3://YOUR-BUCKET/knowledge-base/cholesterol.txt
aws s3 cp knowledge-base/heart-health.txt s3://YOUR-BUCKET/knowledge-base/heart-health.txt
aws s3 cp knowledge-base/basic-health.txt s3://YOUR-BUCKET/knowledge-base/basic-health.txt
```

## Step 6: Create DynamoDB Table

If not already created:

```bash
aws dynamodb create-table \
  --table-name MedAssistEmbeddings \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

## Step 7: Test the Function

### Test with all files

```bash
aws lambda invoke \
  --function-name KnowledgeBaseEmbeddingFunction \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

### Test with specific files

```bash
aws lambda invoke \
  --function-name KnowledgeBaseEmbeddingFunction \
  --payload '{"files": ["diabetes.txt"], "build_faiss_index": true}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

## Step 8: Verify Results

### Check DynamoDB

```bash
aws dynamodb scan \
  --table-name MedAssistEmbeddings \
  --filter-expression "source = :source" \
  --expression-attribute-values '{":source":{"S":"knowledge_base"}}' \
  --select COUNT
```

### Check S3 for FAISS Index

```bash
aws s3 ls s3://YOUR-BUCKET/faiss-indices/
```

You should see:
- `knowledge_base_index.faiss`
- `knowledge_base_metadata.pkl`

### Check CloudWatch Logs

```bash
aws logs tail /aws/lambda/KnowledgeBaseEmbeddingFunction --follow
```

## Step 9: Set Up Scheduled Execution (Optional)

To automatically update the knowledge base on a schedule:

```bash
# Create EventBridge rule
aws events put-rule \
  --name KnowledgeBaseEmbeddingSchedule \
  --schedule-expression "rate(7 days)" \
  --description "Update knowledge base embeddings weekly"

# Add Lambda permission
aws lambda add-permission \
  --function-name KnowledgeBaseEmbeddingFunction \
  --statement-id KnowledgeBaseEmbeddingSchedule \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT-ID:rule/KnowledgeBaseEmbeddingSchedule

# Add target
aws events put-targets \
  --rule KnowledgeBaseEmbeddingSchedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT-ID:function:KnowledgeBaseEmbeddingFunction"
```

## Troubleshooting

### Issue: Timeout Error

**Solution**: Increase Lambda timeout and memory:
```bash
aws lambda update-function-configuration \
  --function-name KnowledgeBaseEmbeddingFunction \
  --timeout 900 \
  --memory-size 3008
```

### Issue: Bedrock Access Denied

**Solution**: Ensure Bedrock model access is enabled in your AWS account:
1. Go to AWS Bedrock console
2. Navigate to Model access
3. Enable access to "Titan Embeddings G1 - Text"

### Issue: FAISS Import Error

**Solution**: Ensure faiss-cpu is included in your deployment package or layer. For Lambda, use faiss-cpu (not faiss-gpu).

### Issue: Out of Memory

**Solution**: Increase Lambda memory allocation. FAISS operations can be memory-intensive:
```bash
aws lambda update-function-configuration \
  --function-name KnowledgeBaseEmbeddingFunction \
  --memory-size 3008
```

## Monitoring

Monitor the function using CloudWatch:

```bash
# View recent invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=KnowledgeBaseEmbeddingFunction \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum

# View errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=KnowledgeBaseEmbeddingFunction \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Cost Considerations

- **Lambda**: Charged per invocation and execution time
- **Bedrock**: Charged per 1000 input tokens for embeddings
- **DynamoDB**: Charged per read/write request (PAY_PER_REQUEST mode)
- **S3**: Minimal storage costs for FAISS indices

Estimated cost for initial knowledge base embedding (5 files, ~50,000 tokens total):
- Lambda: ~$0.10
- Bedrock: ~$0.05
- DynamoDB: ~$0.01
- Total: ~$0.16

## Updates and Maintenance

To update the function code:

```bash
# Update function code
zip -r kb-embedding-function.zip kb_embedding.py faiss_utils.py

aws lambda update-function-code \
  --function-name KnowledgeBaseEmbeddingFunction \
  --zip-file fileb://kb-embedding-function.zip
```

To update environment variables:

```bash
aws lambda update-function-configuration \
  --function-name KnowledgeBaseEmbeddingFunction \
  --environment Variables="{
    KNOWLEDGE_BASE_BUCKET=new-bucket-name,
    EMBEDDINGS_TABLE=new-table-name,
    AWS_REGION=us-east-1
  }"
```
