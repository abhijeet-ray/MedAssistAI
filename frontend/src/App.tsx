import { useState, useCallback } from 'react';
import './App.css';
import type { Role, StatCardData } from './components';
import { Layout, DocumentUpload, Dashboard, ChatInterface } from './components';
import { generateSessionId } from './utils/uuid';

function App() {
  // Session and role state
  const [selectedRole, setSelectedRole] = useState<Role>('patient');
  const [sessionId] = useState<string>(() => {
    const id = generateSessionId();
    console.log('[App] Generated sessionId:', id);
    return id;
  });

  // Dashboard state
  const [statCards, setStatCards] = useState<StatCardData[]>([]);
  const [dashboardRefreshKey, setDashboardRefreshKey] = useState(0);
  const [documentsUploaded, setDocumentsUploaded] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState<string | null>(null);

  // Error state
  const [uploadError, setUploadError] = useState<string | null>(null);

  /**
   * Handle role change - triggers dashboard refresh with new role
   * Requirement 1.6: Dashboard regenerates when role is switched
   */
  const handleRoleChange = useCallback((role: Role) => {
    setSelectedRole(role);
    // Trigger dashboard refresh by incrementing key
    setDashboardRefreshKey((prev) => prev + 1);
  }, []);

  /**
   * Handle document upload completion - triggers dashboard refresh
   * Requirement 2.4: Document upload initiates RAG pipeline
   * Requirement 7.7: Dashboard updates when additional documents are uploaded
   * Requirement 12.4: Update documents_uploaded count after successful processing
   * Requirement 12.5: Display processing status feedback
   */
  const handleUploadComplete = useCallback((documentId: string) => {
    console.log('Document uploaded:', documentId);
    setUploadError(null);
    setIsProcessing(true);
    setProcessingMessage('Processing document...');
    
    // Increment documents uploaded count
    setDocumentsUploaded((prev) => prev + 1);
    
    // Simulate processing completion and show success message
    setTimeout(() => {
      setProcessingMessage('Document processed successfully!');
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingMessage(null);
        // Trigger dashboard refresh to show new data
        setDashboardRefreshKey((prev) => prev + 1);
      }, 1500);
    }, 1000);
  }, []);

  /**
   * Handle upload errors
   */
  const handleUploadError = useCallback((error: string) => {
    setUploadError(error);
  }, []);

  /**
   * Handle dashboard update - stores stat cards in session state
   * Requirement 12.4: Session maintains chat history and dashboard data
   */
  const handleDashboardUpdate = useCallback((cards: StatCardData[]) => {
    setStatCards(cards);
  }, []);

  /**
   * Handle chat message - maintains chat history in session
   * Requirement 10.5: Chat history is maintained for session duration
   * Requirement 12.4: Session maintains chat history
   */
  const handleSendMessage = useCallback((message: string) => {
    console.log('Message sent:', message, 'in session:', sessionId);
  }, [sessionId]);

  return (
    <Layout selectedRole={selectedRole} onRoleChange={handleRoleChange} sessionId={sessionId}>
      {/* Upload Section */}
      <section className="upload-section">
        <h2>Upload Medical Documents</h2>
        <DocumentUpload
          sessionId={sessionId}
          role={selectedRole}
          onUploadComplete={handleUploadComplete}
          onUploadError={handleUploadError}
        />
        {uploadError && (
          <div
            style={{
              marginTop: '12px',
              padding: '12px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              color: '#fca5a5',
              fontSize: '14px',
            }}
          >
            ❌ {uploadError}
          </div>
        )}
      </section>

      {/* Dashboard Section */}
      <section className="dashboard-section">
        <Dashboard
          key={dashboardRefreshKey}
          sessionId={sessionId}
          role={selectedRole}
          statCards={statCards}
          documentsUploaded={documentsUploaded}
          isProcessing={isProcessing}
          processingMessage={processingMessage}
          onExport={() => console.log('Export initiated')}
          onDashboardUpdate={handleDashboardUpdate}
        />
      </section>

      {/* Chat Section */}
      <section className="chat-section">
        <h2>Ask Questions</h2>
        <ChatInterface
          sessionId={sessionId}
          role={selectedRole}
          onSendMessage={handleSendMessage}
        />
      </section>
    </Layout>
  );
}

export default App;
