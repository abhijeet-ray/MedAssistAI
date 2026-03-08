# MedAssist AI Frontend Structure

## Overview

The MedAssist AI frontend is a single-page React application built with TypeScript and Vite. It implements a dark theme with liquid glass styling and provides a role-based interface for medical document analysis.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── RoleSelector.tsx          # Role selection UI (Doctor, Patient, ASHA Worker)
│   │   ├── RoleSelector.test.tsx     # Unit tests for RoleSelector
│   │   ├── DocumentUpload.tsx        # File upload component with drag-and-drop
│   │   ├── DocumentUpload.test.tsx   # Unit tests for DocumentUpload
│   │   ├── Dashboard.tsx             # Dashboard with stat cards and export
│   │   ├── Dashboard.test.tsx        # Unit tests for Dashboard
│   │   ├── StatCard.tsx              # Individual stat card component
│   │   ├── ChatInterface.tsx         # ChatGPT-style chat interface
│   │   ├── ChatInterface.test.tsx    # Unit tests for ChatInterface
│   │   ├── Layout.tsx                # Main layout with sidebar and workspace
│   │   └── index.ts                  # Component exports
│   ├── utils/
│   │   └── api.ts                    # API client for backend communication
│   ├── App.tsx                       # Main application component
│   ├── App.css                       # Dark theme and styling
│   └── main.tsx                      # Application entry point
├── public/
│   └── index.html                    # HTML template
├── .env.example                      # Environment variables template
├── package.json                      # Dependencies and scripts
├── tsconfig.json                     # TypeScript configuration
├── vite.config.ts                    # Vite configuration
└── FRONTEND_STRUCTURE.md             # This file
```

## Components

### RoleSelector
- **Purpose**: Allows users to select their role (Doctor, Patient, ASHA Worker)
- **Props**: `selectedRole`, `onRoleChange`
- **Features**: Three role buttons with active state styling
- **Requirements**: 1.1

### DocumentUpload
- **Purpose**: Handles document upload with drag-and-drop support
- **Props**: `onUploadComplete`, `onUploadError`
- **Features**: 
  - Accepts PDF, JPEG, PNG files
  - Drag-and-drop support
  - Upload progress indicator
  - File type validation
- **Requirements**: 2.1, 2.2, 2.6

### Dashboard
- **Purpose**: Displays health insights as stat cards
- **Props**: `statCards`, `onExport`
- **Features**:
  - Grid layout for stat cards
  - Export to PDF button
  - Medical disclaimer
  - Severity-based color coding
- **Requirements**: 7.1, 14.4, 14.6, 20.2, 20.3

### StatCard
- **Purpose**: Individual health metric card
- **Props**: `data` (StatCardData)
- **Features**:
  - Title, value, unit, insight display
  - Severity-based styling (normal, warning, critical)
  - Hover effects
- **Requirements**: 14.6

### ChatInterface
- **Purpose**: ChatGPT-style conversational interface
- **Props**: `onSendMessage`
- **Features**:
  - Message input with 1000 character limit
  - Chat history display
  - Typing indicator
  - Medical disclaimer on first interaction
  - Auto-scroll to latest message
- **Requirements**: 10.1-10.7, 14.4, 14.5, 20.5

### Layout
- **Purpose**: Main application layout with sidebar and workspace
- **Props**: `selectedRole`, `onRoleChange`, `sessionId`, `children`
- **Features**:
  - Sidebar with role selector
  - Main workspace area
  - Medical disclaimer header
  - Session info footer
- **Requirements**: 14.1, 14.2, 14.3, 14.4

## Styling

### Dark Theme Variables
- `--bg-primary`: #0a0a0f (main background)
- `--bg-secondary`: #1a1a2e (secondary background)
- `--bg-glass`: rgba(26, 26, 46, 0.7) (glass effect)
- `--text-primary`: #e0e0e0 (main text)
- `--text-secondary`: #a0a0a0 (secondary text)
- `--accent-primary`: #6366f1 (primary accent)
- `--accent-hover`: #818cf8 (hover accent)
- `--success`: #10b981 (success color)
- `--warning`: #f59e0b (warning color)
- `--error`: #ef4444 (error color)

### Liquid Glass Effect
- Uses `backdrop-filter: blur(20px)` for glass morphism
- Semi-transparent backgrounds with rgba colors
- Smooth transitions and hover effects

## API Integration

The frontend communicates with the backend through AWS API Gateway endpoints:

### Endpoints
- `POST /upload` - Upload medical documents
- `POST /chat` - Send chat messages
- `GET /dashboard` - Fetch dashboard data
- `POST /export` - Export dashboard as PDF

### API Client
Located in `src/utils/api.ts`, provides:
- `uploadDocument()` - Upload file
- `sendChatMessage()` - Send chat message
- `fetchDashboard()` - Get dashboard data
- `exportDashboardPDF()` - Export to PDF

## Environment Variables

Create a `.env` file based on `.env.example`:

```
VITE_API_ENDPOINT=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

## Development

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

### Run Tests
```bash
npm test
```

### Lint Code
```bash
npm run lint
```

## Requirements Coverage

### Requirement 14: User Interface Design
- ✅ 14.1: Single-page React application architecture
- ✅ 14.2: Dark theme with liquid glass styling
- ✅ 14.3: Sidebar containing role selector
- ✅ 14.4: Main workspace with upload, dashboard, and chat
- ✅ 14.5: ChatGPT-style chat interface
- ✅ 14.6: Card-based stat card layouts

### Requirement 1: Role Selection
- ✅ 1.1: Three role options (Doctor, Patient, ASHA Worker)
- 🔄 1.2: Interface configuration on role selection (backend integration needed)
- 🔄 1.3-1.5: Language and complexity configuration (backend integration needed)
- 🔄 1.6: Dashboard regeneration on role switch (backend integration needed)

### Requirement 2: Document Upload
- ✅ 2.1: Accept PDF files
- ✅ 2.2: Accept JPEG and PNG files
- 🔄 2.3: Store in S3 (backend integration needed)
- 🔄 2.4: Initiate RAG pipeline (backend integration needed)
- 🔄 2.5: Process multiple documents (backend integration needed)
- ✅ 2.6: Display upload progress

### Requirement 7: Dashboard Generation
- ✅ 7.1: Dashboard with stat cards
- 🔄 7.2-7.6: Specific metric cards (backend integration needed)
- 🔄 7.7: Update on additional uploads (backend integration needed)
- 🔄 7.8: Role-appropriate summaries (backend integration needed)

### Requirement 10: Chat Interface
- ✅ 10.1: Chat interface component
- ✅ 10.2: Text input up to 1000 characters
- ✅ 10.3: Display user messages
- ✅ 10.4: Display AI responses
- 🔄 10.5: Maintain chat history (backend integration needed)
- 🔄 10.6-10.7: Document and knowledge base queries (backend integration needed)

### Requirement 13: Export Dashboard Report
- 🔄 13.1: Export button (UI ready, backend integration needed)
- 🔄 13.2-13.6: PDF generation and download (backend integration needed)

### Requirement 20: Responsible AI Disclaimer
- ✅ 20.1: Disclaimer on initial load
- ✅ 20.2: Disclaimer in dashboard
- ✅ 20.5: Disclaimer on first chat interaction

## Testing

Unit tests are provided for all components using Vitest and React Testing Library:

- `RoleSelector.test.tsx` - Tests role selection functionality
- `DocumentUpload.test.tsx` - Tests file upload and validation
- `Dashboard.test.tsx` - Tests dashboard display and export
- `ChatInterface.test.tsx` - Tests chat functionality

To run tests:
```bash
npm test
```

## Next Steps

1. **Backend Integration**: Connect API endpoints to actual backend services
2. **State Management**: Consider adding Redux or Zustand for complex state
3. **Error Handling**: Implement comprehensive error handling for API failures
4. **Accessibility**: Add ARIA labels and keyboard navigation
5. **Performance**: Optimize bundle size and lazy load components
6. **Internationalization**: Add Hindi translation support for Patient and ASHA Worker roles
7. **PWA**: Convert to Progressive Web App for offline support

## Notes

- The frontend is fully typed with TypeScript
- All components are functional components with hooks
- Styling uses CSS variables for easy theming
- The application is responsive and works on desktop and tablet
- Session management is handled through UUID generation
- API calls are mocked in components for development (TODO: replace with actual API calls)
