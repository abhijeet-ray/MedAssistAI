# MedAssist AI - Medical Document Analysis System

A full-stack AI-powered medical document analysis system built with React, AWS Lambda, and Google Gemini API. The system extracts health metrics from medical documents and provides role-based conversational AI assistance.

## Features

- **Document Upload & Processing**: Upload PDF and image documents for automatic text extraction
- **Health Metrics Extraction**: Automatically extract key health metrics (glucose, hemoglobin, cholesterol, etc.)
- **Hybrid RAG Architecture**: Combines document embeddings with knowledge base for intelligent responses
- **Role-Based Interface**: Customized experience for Doctors, Patients, and ASHA Workers
- **Conversational AI**: Multi-turn chat with context awareness using Google Gemini
- **Hindi Translation**: Support for Hindi language translation for Patient and ASHA Worker roles
- **PDF Export**: Generate and download health reports as PDF
- **Real-time Dashboard**: Visual display of extracted health metrics with status indicators

## Architecture

```
MedAssist-AI/
├── frontend/              # React TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── utils/        # Utility functions
│   │   └── App.tsx       # Main app component
│   └── package.json
├── lambda/               # AWS Lambda functions
│   ├── upload/          # Document upload handler
│   ├── extraction/      # Text extraction from documents
│   ├── embedding/       # Vector embedding generation
│   ├── dashboard/       # Dashboard metrics generation
│   ├── rag/            # Chat/RAG handler
│   ├── export/         # PDF export handler
│   └── cleanup/        # Session cleanup
├── infrastructure/       # AWS CDK infrastructure
│   ├── lib/
│   │   └── medassist-stack.ts
│   └── package.json
├── knowledge-base/       # Medical knowledge base files
│   ├── diabetes.txt
│   ├── blood-pressure.txt
│   ├── cholesterol.txt
│   ├── heart-health.txt
│   └── basic-health.txt
└── README.md
```

## Tech Stack

**Frontend:**
- React 18 with TypeScript
- Vite for build tooling
- Vitest for testing
- Tailwind CSS for styling

**Backend:**
- AWS Lambda (Python)
- AWS API Gateway
- AWS DynamoDB
- AWS S3
- AWS Textract (document extraction)
- AWS Comprehend Medical (entity extraction)
- Google Gemini API (AI responses)
- FAISS (vector search)

**Infrastructure:**
- AWS CDK (TypeScript)
- CloudWatch for logging

## Setup & Deployment

### Prerequisites
- Node.js 18+
- Python 3.9+
- AWS Account with appropriate permissions
- Google Gemini API key

### Environment Variables

Create `.env` files in the appropriate directories:

**Frontend (.env):**
```
VITE_API_ENDPOINT=https://your-api-gateway-url
```

**Lambda Functions:**
Set these in AWS Lambda environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `DOCUMENT_TABLE`: DynamoDB table name for documents
- `CHAT_HISTORY_TABLE`: DynamoDB table name for chat history
- `EMBEDDINGS_TABLE`: DynamoDB table name for embeddings

### Installation

1. **Frontend Setup:**
```bash
cd frontend
npm install
npm run build
```

2. **Lambda Setup:**
```bash
cd lambda
# Install dependencies for each Lambda function
cd rag && pip install -r requirements.txt
cd ../dashboard && pip install -r requirements.txt
# ... repeat for other Lambda functions
```

3. **Infrastructure Deployment:**
```bash
cd infrastructure
npm install
cdk deploy
```

## API Endpoints

### Upload Document
```
POST /upload
Body: { file: File, sessionId: string }
Response: { documentId: string, status: string }
```

### Chat/RAG
```
POST /chat
Body: { 
  sessionId: string, 
  message: string, 
  role: 'doctor' | 'patient' | 'asha',
  chatHistory: Array
}
Response: { answer: string, chatHistory: Array }
```

### Get Dashboard
```
GET /dashboard?sessionId=<sessionId>
Response: { metrics: Array, timestamp: string }
```

### Export PDF
```
POST /export
Body: { sessionId: string }
Response: { pdfUrl: string }
```

## Testing

### Frontend Tests
```bash
cd frontend
npm run test
```

### Lambda Tests
```bash
cd lambda/rag
pytest tests/
```

## Security

- All API keys are stored in AWS Lambda environment variables (not in code)
- CORS is configured for API Gateway
- S3 buckets use AES-256 encryption
- DynamoDB tables use encryption at rest
- IAM roles follow least privilege principle
- Sensitive medical data is redacted from logs

## Performance

- Dashboard Lambda: <500ms
- Chat Lambda: <3s
- Dashboard Component render: <100ms
- FAISS search: <500ms for 10,000 vectors

## Correctness Properties

The system implements 36 correctness properties validated through property-based testing:

1. Metric Extraction Completeness
2. Reference Range Assignment
3. Status Indicator Accuracy
4. Most Recent Metric Aggregation
5. Multiple Document Context Combination
6. Metric Category Grouping
7. Missing Metrics Not Displayed
8. Chat Response Structure Completeness
9. Important Findings Array Bounds
10. Suggested Action Array Bounds
... and 26 more properties

See `.kiro/specs/health-insights-ux-improvements/` for detailed specifications.

## Documentation

- **Requirements**: `.kiro/specs/health-insights-ux-improvements/requirements.md`
- **Design**: `.kiro/specs/health-insights-ux-improvements/design.md`
- **Tasks**: `.kiro/specs/health-insights-ux-improvements/tasks.md`

## Disclaimer

This AI system provides informational insights only and does not provide medical diagnosis. Always consult a licensed healthcare professional.

## License

This project is provided for educational and evaluation purposes.

## Support

For questions or issues, please refer to the specification documents in `.kiro/specs/`.
