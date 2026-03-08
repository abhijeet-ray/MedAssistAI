/**
 * Generate a unique session ID with fallback for browsers that don't support crypto.randomUUID
 * 
 * This function provides a safe UUID generator that works across all browsers:
 * - Modern browsers: Uses crypto.randomUUID() (RFC 4122 compliant)
 * - Older browsers: Falls back to timestamp + random string
 */
export function generateSessionId(): string {
  // Check if crypto.randomUUID is available (modern browsers)
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  
  // Fallback for older browsers or environments without crypto.randomUUID
  return "session-" + Date.now() + "-" + Math.random().toString(36).substring(2, 9);
}
