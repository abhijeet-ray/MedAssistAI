🏥 MedAssist AI

AI-Powered Medical Document Intelligence Platform

MedAssist AI is a Generative AI powered medical document analysis system that helps users understand complex medical reports.

The platform analyzes uploaded health documents and converts them into structured insights, health dashboards, and conversational explanations.

It is designed for Doctors, Patients, and ASHA Workers to simplify healthcare understanding.

📌 Problem

Medical reports are often difficult for non-experts to interpret.

Patients frequently struggle to understand values such as:

Blood Glucose

Hemoglobin

Cholesterol

Blood Pressure

Liver & Kidney indicators

In rural healthcare systems, ASHA workers also lack tools to quickly interpret reports for patients.

This creates a knowledge gap between medical reports and actionable understanding.

💡 Solution

MedAssist AI bridges this gap using Generative AI and Retrieval Augmented Generation (RAG).

The system:

Extracts medical data from uploaded reports

Identifies key health metrics

Generates a visual health dashboard

Allows users to ask questions about their report

Provides role-specific explanations for doctors, patients, and community health workers

🚀 Key Features

✔ Medical document upload (PDF / Images)
✔ AI-powered health metric extraction
✔ Generative AI conversational assistant
✔ Role-based explanations (Doctor / Patient / ASHA Worker)
✔ Health dashboard with structured indicators
✔ AI-driven report insights
✔ Exportable health report summary
✔ Secure serverless architecture

🧠 AI Architecture

MedAssist AI uses a Retrieval Augmented Generation (RAG) pipeline.

Workflow:

1️⃣ User uploads medical document
2️⃣ Document text is extracted using AWS AI services
3️⃣ Relevant medical context is retrieved from knowledge sources
4️⃣ Generative AI model produces structured insights
5️⃣ Results are presented as:

Health dashboard

Conversational AI responses

Actionable health explanations

This ensures AI responses are grounded in the user's document data.

⚙️ System Architecture
User
 │
 ▼
React Web Application
 │
 ▼
AWS CloudFront + S3 (Frontend Hosting)
 │
 ▼
API Gateway
 │
 ▼
AWS Lambda Functions
 │
 ├── Upload Service
 ├── Extraction Service
 ├── Dashboard Generator
 ├── RAG Chat Engine
 └── PDF Export Service
 │
 ▼
AI Processing Layer
 ├── Document Intelligence
 ├── Retrieval Engine
 └── Generative AI Model
 │
 ▼
Storage Layer
 ├── DynamoDB
 └── Amazon S3
☁️ AWS Services Used

MedAssist AI is built using serverless AWS infrastructure.

Core services:

AWS Lambda

Amazon API Gateway

Amazon S3

Amazon DynamoDB

AWS Textract

AWS Comprehend Medical

Amazon CloudFront

AWS CloudWatch

AWS CDK

These services enable a scalable, secure, and fully serverless AI architecture.

🧰 Tech Stack
Frontend

React

TypeScript

Vite

TailwindCSS

Backend

Python (AWS Lambda)

REST APIs via API Gateway

Serverless architecture

AI Layer

Retrieval Augmented Generation (RAG)

Medical document processing

Generative AI inference

Infrastructure

AWS CDK

CloudWatch monitoring

📂 Project Structure
MedAssist-AI/
│
├── frontend/                    # React web application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── utils/
│   │   └── App.tsx
│   └── package.json
│
├── lambda/                      # Serverless backend functions
│   ├── upload/                  # Document upload handler
│   ├── extraction/              # Medical text extraction
│   ├── embedding/               # Document processing
│   ├── dashboard/               # Dashboard generation
│   ├── rag/                     # AI chat engine
│   ├── export/                  # PDF export generator
│   └── cleanup/                 # Session cleanup
│
├── infrastructure/              # AWS CDK infrastructure
│   ├── lib/
│   │   └── medassist-stack.ts
│   └── package.json
│
├── knowledge-base/              # Medical knowledge resources
│   ├── diabetes.txt
│   ├── blood-pressure.txt
│   ├── cholesterol.txt
│   ├── heart-health.txt
│   └── basic-health.txt
│
└── README.md
🔗 API Endpoints
Upload Document
POST /upload
Chat with AI
POST /chat
Get Dashboard
GET /dashboard?sessionId=<sessionId>
Export Report
POST /export
🛠 Deployment

The system uses serverless deployment on AWS.

Infrastructure deployment:

cd infrastructure
npm install
cdk deploy

Frontend deployment:

cd frontend
npm install
npm run build
🔐 Security

API keys stored in environment variables

S3 encryption enabled

DynamoDB encryption at rest

IAM least-privilege access

Sensitive medical data excluded from logs

📊 Performance

Typical system response times:

Dashboard generation: <500 ms
AI chat response: ~2-3 seconds
Document extraction: 1-3 seconds

⚠️ Disclaimer

MedAssist AI provides informational insights only and does not provide medical diagnosis.

Users should always consult licensed healthcare professionals.

📜 License

Educational and evaluation purposes.
