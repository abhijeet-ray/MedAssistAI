# 🏥 MedAssist AI

**AI-Powered Medical Document Analysis & Conversational Health Assistant**

MedAssist AI is a full-stack AI system that helps users **understand complex medical reports**.
The system analyzes uploaded medical documents and converts them into **clear insights, dashboards, and conversational explanations**.

It is designed for **Doctors, Patients, and ASHA Workers** to make healthcare information easier to understand.

---

# 📌 Problem

Medical reports are difficult for non-experts to interpret.

Patients often struggle to understand values such as:

* Blood Glucose
* Hemoglobin
* Cholesterol
* Blood Pressure
* Liver & Kidney indicators

In rural healthcare systems, **ASHA workers also lack tools** to quickly interpret reports for patients.

---

# 💡 Solution

MedAssist AI automatically analyzes medical documents and generates **easy-to-understand health insights using AI**.

The system:

1. Extracts medical text from uploaded reports
2. Identifies key health metrics
3. Generates a visual health dashboard
4. Allows users to chat with an AI assistant about the report
5. Explains results differently for **Doctor / Patient / ASHA Worker**

---

# 🚀 Key Features

✔ Medical document upload (PDF / Image)
✔ Automatic text extraction using AWS Textract
✔ Health metric extraction (Glucose, Hemoglobin, Cholesterol, etc.)
✔ AI conversational assistant
✔ Role-based explanation system
✔ Health dashboard with status indicators
✔ PDF report export
✔ Secure serverless architecture

---

# ⚙️ System Architecture

User uploads report → AI extracts insights → Dashboard + Chat explanation

```
User Browser
     │
     ▼
React Frontend
     │
     ▼
AWS CloudFront / S3
     │
     ▼
API Gateway
     │
     ▼
AWS Lambda Functions
     │
     ├── Document Upload
     ├── Text Extraction
     ├── Dashboard Generation
     ├── AI Chat (RAG)
     └── PDF Export
     │
     ▼
AI Processing
     ├── Google Gemini API
     ├── AWS Textract
     └── Medical Knowledge Base
     │
     ▼
Data Storage
     ├── DynamoDB
     └── Amazon S3
```

---

# 🧠 AI Components

MedAssist AI uses **Hybrid RAG (Retrieval Augmented Generation)**.

Steps:

1. Medical document uploaded
2. Text extracted using AWS Textract
3. Relevant information retrieved from document + knowledge base
4. AI model generates explanation using Gemini API
5. Role-specific explanation returned

---

# 🧰 Tech Stack

## Frontend

* React
* TypeScript
* Vite
* TailwindCSS

## Backend

* AWS Lambda (Python)
* AWS API Gateway
* AWS DynamoDB
* AWS S3

## AI & Data Processing

* Google Gemini API
* AWS Textract
* FAISS Vector Search
* Hybrid RAG Architecture

## Infrastructure

* AWS CDK
* CloudWatch Monitoring

---

# 📂 Project Structure

```
MedAssist-AI/
│
├── frontend/                     # React frontend application
│   ├── src/
│   │   ├── components/           # UI components
│   │   ├── pages/                # Application pages
│   │   ├── utils/                # Helper utilities
│   │   └── App.tsx               # Main React app
│   └── package.json
│
├── lambda/                       # AWS Lambda functions
│   ├── upload/                   # Document upload handler
│   ├── extraction/               # Text extraction from documents
│   ├── embedding/                # Embedding generation
│   ├── dashboard/                # Dashboard metrics generation
│   ├── rag/                      # Chat / RAG handler
│   ├── export/                   # PDF export generator
│   └── cleanup/                  # Session cleanup
│
├── infrastructure/               # AWS infrastructure
│   ├── lib/
│   │   └── medassist-stack.ts    # CDK stack
│   └── package.json
│
├── knowledge-base/               # Medical knowledge documents
│   ├── diabetes.txt
│   ├── blood-pressure.txt
│   ├── cholesterol.txt
│   ├── heart-health.txt
│   └── basic-health.txt
│
└── README.md
```

---

# 🔗 API Endpoints

### Upload Medical Document

```
POST /upload
```

Body

```
{
  "file": File,
  "sessionId": "string"
}
```

---

### Chat with AI Assistant

```
POST /chat
```

Body

```
{
  "sessionId": "string",
  "message": "string",
  "role": "doctor | patient | asha"
}
```

---

### Get Health Dashboard

```
GET /dashboard?sessionId=<sessionId>
```

---

### Export Report

```
POST /export
```

---

# 🛠 Setup & Deployment

## Prerequisites

* Node.js 18+
* Python 3.9+
* AWS account
* Google Gemini API Key

---

## Frontend Setup

```
cd frontend
npm install
npm run build
```

---

## Backend Setup

```
cd lambda
pip install -r requirements.txt
```

---

## Deploy Infrastructure

```
cd infrastructure
npm install
cdk deploy
```

---

# 🔐 Security

* API keys stored in environment variables
* S3 encryption enabled
* DynamoDB encryption at rest
* IAM least privilege access
* Sensitive data removed from logs

---

# 📊 Performance

Typical response times:

Dashboard generation: **<500ms**
Chat response: **~3 seconds**
Document extraction: **1–3 seconds**

---

# ⚠️ Disclaimer

This AI system provides **informational insights only** and does **not provide medical diagnosis**.

Users should always consult licensed healthcare professionals.

---

# 📜 License

This project is provided for **educational and evaluation purposes**.
