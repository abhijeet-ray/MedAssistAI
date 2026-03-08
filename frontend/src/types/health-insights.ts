/**
 * Health Insights UX Improvements - Core Data Models
 * Defines TypeScript interfaces for health metrics, chat responses, and API contracts
 */

/**
 * Status indicator for health metrics
 * - Normal: Value within reference range
 * - Low: Value below reference range
 * - High: Value above reference range
 * - Critical: Value significantly outside reference range (>30% deviation)
 */
export type StatusIndicator = 'Normal' | 'Low' | 'High' | 'Critical';

/**
 * Health metric extracted from medical documents
 * Represents a single quantifiable medical parameter with reference ranges and status
 */
export interface HealthMetric {
  metric_name: string;                    // e.g., "Hemoglobin"
  value: number;                          // e.g., 14.5
  unit: string;                           // e.g., "g/dL"
  reference_range_min: number;            // e.g., 13.5
  reference_range_max: number;            // e.g., 17.5
  status_indicator: StatusIndicator;      // Normal, Low, High, or Critical
  extraction_timestamp: string;           // ISO8601 format
  category: string;                       // e.g., "Blood_Work", "Metabolic_Panel", "Thyroid_Function"
  document_id?: string;                   // Optional reference to source document
}

/**
 * Structured chat response with four distinct sections
 * Provides organized, scannable AI responses to user queries
 */
export interface ChatResponse {
  summary: string;                        // 1-2 sentence overview
  important_findings: string[];           // 3-7 key findings as bullet points
  what_it_means: string;                  // 2-3 sentences explaining clinical significance
  suggested_action: string[];             // 1-3 actionable recommendations
  timestamp: string;                      // ISO8601 format
  conversationId: string;                 // Reference to conversation
}

/**
 * Single message in a chat conversation
 * Maintains role, content, and optional structured response for AI messages
 */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;                      // ISO8601 format
  structuredResponse?: ChatResponse;      // Only for assistant messages
}

/**
 * Context window for managing conversation history
 * Maintains last 3 messages in memory to inform AI responses
 * Helps reduce repetition and provide contextual awareness
 */
export interface ContextWindow {
  conversationId: string;
  userId: string;
  messages: ChatMessage[];                // Last 3 messages (max)
  lastUpdated: string;                    // ISO8601 format
  expiresAt: string;                      // ISO8601 format (session end)
}

/**
 * Dashboard API response containing extracted health metrics
 * Provides structured data for frontend dashboard rendering
 */
export interface DashboardApiResponse {
  metrics: HealthMetric[];
  document_count: number;
  word_count: number;
  extraction_timestamp: string;           // ISO8601 format
  status: 'success' | 'partial' | 'error';
  message?: string;
}

/**
 * Chat API response containing structured chat response
 * Provides validated structured response with context information
 */
export interface ChatApiResponse {
  response: ChatResponse;
  context_window_size: number;
  retry_count: number;
  timestamp: string;                      // ISO8601 format
  status: 'success' | 'error';
  error_message?: string;
}

/**
 * Generic API error response
 * Standardized error format for all API endpoints
 */
export interface ApiError {
  code: string;
  message: string;
  retryable: boolean;
  timestamp?: string;
}

/**
 * Metric categories for organizing health metrics
 */
export const METRIC_CATEGORIES = {
  BLOOD_WORK: 'Blood_Work',
  METABOLIC_PANEL: 'Metabolic_Panel',
  THYROID_FUNCTION: 'Thyroid_Function',
} as const;

/**
 * Reference ranges for standard medical metrics
 * Used when document doesn't provide explicit ranges
 */
export const REFERENCE_RANGES = {
  Hemoglobin: { min: 13.5, max: 17.5, unit: 'g/dL', category: METRIC_CATEGORIES.BLOOD_WORK },
  WBC: { min: 4.5, max: 11.0, unit: 'K/uL', category: METRIC_CATEGORIES.BLOOD_WORK },
  Platelets: { min: 150, max: 400, unit: 'K/uL', category: METRIC_CATEGORIES.BLOOD_WORK },
  'Blood Glucose': { min: 70, max: 100, unit: 'mg/dL', category: METRIC_CATEGORIES.METABOLIC_PANEL },
  Cholesterol: { min: 0, max: 200, unit: 'mg/dL', category: METRIC_CATEGORIES.METABOLIC_PANEL },
  TSH: { min: 0.4, max: 4.0, unit: 'mIU/L', category: METRIC_CATEGORIES.THYROID_FUNCTION },
} as const;
