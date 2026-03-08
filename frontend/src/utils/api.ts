/**
 * API client for MedAssist AI System
 * Communicates with AWS API Gateway endpoints
 */

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT || '/api';

interface ApiResponse<T> {
  data?: T;
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  };
}

/**
 * Upload a medical document
 */
export async function uploadDocument(
  sessionId: string,
  role: string,
  file: File
): Promise<ApiResponse<{ documentId: string; status: string }>> {
  try {
    console.log('[API] Upload - sessionId:', sessionId, 'role:', role, 'file:', file.name);
    
    // Convert file to base64
    const base64File = await fileToBase64(file);

    const requestBody = {
      sessionId,
      role,
      file: base64File,
      filename: file.name,
      contentType: file.type,
    };
    
    console.log('[API] Upload request body keys:', Object.keys(requestBody));

    const response = await fetch(`${API_ENDPOINT}/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      return { error };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return {
      error: {
        code: 'UPLOAD_ERROR',
        message: error instanceof Error ? error.message : 'Failed to upload document',
        retryable: true,
      },
    };
  }
}

/**
 * Helper function to convert File to base64
 */
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      // Remove the data URL prefix (e.g., "data:application/pdf;base64,")
      const base64Data = base64.split(',')[1];
      resolve(base64Data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Send a chat message with conversation history
 */
export async function sendChatMessage(
  sessionId: string,
  role: string,
  message: string,
  chatHistory: Array<{ user: string; ai: string }> = []
): Promise<ApiResponse<{ answer: string; source: string; chatHistory: Array<{ user: string; ai: string }> }>> {
  try {
    const requestBody = {
      sessionId,
      role,
      message,
      chatHistory,
    };
    
    console.log('[API] Chat - sessionId:', sessionId, 'role:', role, 'message:', message.substring(0, 50), 'history length:', chatHistory.length);

    const response = await fetch(`${API_ENDPOINT}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      return { error };
    }

    const data = await response.json();
    
    // Handle the response format from backend
    if (data.answer) {
      return { 
        data: { 
          answer: data.answer, 
          source: data.source,
          chatHistory: data.chatHistory || chatHistory
        } 
      };
    }
    
    // Handle error response
    if (data.error) {
      return { error: data.error };
    }
    
    return { data };
  } catch (error) {
    return {
      error: {
        code: 'CHAT_ERROR',
        message: error instanceof Error ? error.message : 'Failed to send message',
        retryable: true,
      },
    };
  }
}

/**
 * Fetch dashboard data
 */
export async function fetchDashboard(
  sessionId: string,
  role: string,
  language: 'en' | 'hi' = 'en'
): Promise<
  ApiResponse<{
    statCards: Array<{
      title: string;
      value: string;
      unit: string;
      insight: string;
      severity: 'normal' | 'warning' | 'critical';
    }>;
    lastUpdated: string;
  }>
> {
  try {
    const params = new URLSearchParams({
      sessionId,
      role,
      language,
    });
    
    const url = `${API_ENDPOINT}/dashboard?${params}`;
    console.log('[API] Dashboard - URL:', url);
    console.log('[API] Dashboard - sessionId:', sessionId, 'role:', role);

    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const error = await response.json();
      return { error };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return {
      error: {
        code: 'DASHBOARD_ERROR',
        message: error instanceof Error ? error.message : 'Failed to fetch dashboard',
        retryable: true,
      },
    };
  }
}

/**
 * Export dashboard as PDF
 */
export async function exportDashboardPDF(
  sessionId: string,
  role: string,
  language: 'en' | 'hi' = 'en',
  statCards: Array<{
    title: string;
    value: string;
    unit: string;
    insight: string;
    severity: 'normal' | 'warning' | 'critical';
  }> = []
): Promise<ApiResponse<{ pdfUrl: string; expiresAt: string }>> {
  try {
    const requestBody = {
      sessionId,
      role,
      language,
      statCards,
    };
    
    console.log('[API] Export - sessionId:', sessionId, 'role:', role, 'statCards count:', statCards.length);
    console.log('[API] Export request body keys:', Object.keys(requestBody));

    const response = await fetch(`${API_ENDPOINT}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      return { error };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return {
      error: {
        code: 'EXPORT_ERROR',
        message: error instanceof Error ? error.message : 'Failed to export PDF',
        retryable: true,
      },
    };
  }
}
