/**
 * Chat Response Formatter
 * Parses AI responses and structures them into 4 sections:
 * Summary, Important Findings, What It Means, Suggested Action
 */

export interface FormattedChatResponse {
  summary: string;
  importantFindings: string[];
  whatItMeans: string;
  suggestedAction: string[];
  isFormatted: boolean;
}

/**
 * Parse AI response text and extract structured sections
 * Looks for common section headers and patterns
 */
export function formatChatResponse(responseText: string): FormattedChatResponse {
  if (!responseText || typeof responseText !== 'string') {
    return {
      summary: responseText || '',
      importantFindings: [],
      whatItMeans: '',
      suggestedAction: [],
      isFormatted: false,
    };
  }

  // Split by section markers (case-insensitive, with optional colon)
  const sections = splitBySectionMarkers(responseText);

  if (sections.summary || sections.findings || sections.means || sections.action) {
    const importantFindings = parseBulletPoints(sections.findings);
    const suggestedAction = parseBulletPoints(sections.action);

    // If we successfully extracted at least some sections, return formatted response
    if (sections.summary || importantFindings.length > 0 || sections.means || suggestedAction.length > 0) {
      return {
        summary: sections.summary.trim(),
        importantFindings,
        whatItMeans: sections.means.trim(),
        suggestedAction,
        isFormatted: true,
      };
    }
  }

  // Fallback: if no structured sections found, try to split by sentences
  // and create a basic structure
  const sentences = responseText.split(/(?<=[.!?])\s+/).filter((s) => s.trim());

  if (sentences.length > 0) {
    // First sentence as summary
    const summary = sentences[0];

    // Look for bullet points or numbered items in the entire text
    const importantFindings = parseBulletPoints(responseText);

    // Remaining sentences as "What It Means"
    const whatItMeans = sentences.slice(1, Math.min(3, sentences.length)).join(' ');

    return {
      summary,
      importantFindings,
      whatItMeans,
      suggestedAction: [],
      isFormatted: false,
    };
  }

  // Last resort: return entire text as summary
  return {
    summary: responseText,
    importantFindings: [],
    whatItMeans: '',
    suggestedAction: [],
    isFormatted: false,
  };
}

/**
 * Split response text by section markers
 * Handles: "Summary:", "Important Findings:", "What It Means:", "Suggested Action:"
 */
function splitBySectionMarkers(text: string): {
  summary: string;
  findings: string;
  means: string;
  action: string;
} {
  const result = {
    summary: '',
    findings: '',
    means: '',
    action: '',
  };

  // Create regex patterns for section markers (case-insensitive)
  const summaryRegex = /summary\s*:\s*([\s\S]*?)(?=important\s+findings\s*:|what\s+it\s+means\s*:|suggested\s+action\s*:|$)/i;
  const findingsRegex = /important\s+findings\s*:\s*([\s\S]*?)(?=what\s+it\s+means\s*:|suggested\s+action\s*:|$)/i;
  const meansRegex = /what\s+it\s+means\s*:\s*([\s\S]*?)(?=suggested\s+action\s*:|$)/i;
  const actionRegex = /suggested\s+action\s*:\s*([\s\S]*?)$/i;

  const summaryMatch = text.match(summaryRegex);
  const findingsMatch = text.match(findingsRegex);
  const meansMatch = text.match(meansRegex);
  const actionMatch = text.match(actionRegex);

  if (summaryMatch) result.summary = summaryMatch[1];
  if (findingsMatch) result.findings = findingsMatch[1];
  if (meansMatch) result.means = meansMatch[1];
  if (actionMatch) result.action = actionMatch[1];

  return result;
}

/**
 * Parse bullet points or numbered items from text
 * Handles formats like:
 * - Item 1
 * • Item 2
 * * Item 3
 * 1. Item 4
 * 1) Item 5
 */
function parseBulletPoints(text: string): string[] {
  if (!text || typeof text !== 'string') {
    return [];
  }

  // Match lines starting with bullet points or numbers
  const bulletPattern = /^[\s]*[-•*]\s+(.+)$/gm;
  const numberedPattern = /^[\s]*\d+[.)]\s+(.+)$/gm;

  const bullets = Array.from(text.matchAll(bulletPattern), (m) => m[1].trim());
  const numbered = Array.from(text.matchAll(numberedPattern), (m) => m[1].trim());

  const items = [...bullets, ...numbered];

  // If no structured bullets found, try splitting by newlines and filter non-empty
  if (items.length === 0) {
    return text
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0 && line.length < 200);
  }

  return items;
}

/**
 * Check if response appears to be already formatted
 */
export function isAlreadyFormatted(responseText: string): boolean {
  if (!responseText) return false;

  const hasHeaders =
    /summary|important\s+findings|what\s+it\s+means|suggested\s+action/i.test(responseText);
  const hasBullets = /^[\s]*[-•*]\s+/m.test(responseText);
  const hasNumbered = /^[\s]*\d+[.)]\s+/m.test(responseText);

  return hasHeaders || hasBullets || hasNumbered;
}

/**
 * Check if two responses are duplicates
 * Compares normalized versions (lowercase, trimmed, extra whitespace removed)
 */
export function isDuplicateResponse(currentResponse: string, previousResponse: string): boolean {
  if (!currentResponse || !previousResponse) return false;

  // Normalize both responses for comparison
  const normalize = (text: string) =>
    text
      .toLowerCase()
      .trim()
      .replace(/\s+/g, ' ')
      .replace(/[^\w\s]/g, '');

  const normalizedCurrent = normalize(currentResponse);
  const normalizedPrevious = normalize(previousResponse);

  // Check for exact match or very high similarity (>95%)
  if (normalizedCurrent === normalizedPrevious) return true;

  // Calculate similarity ratio
  const similarity = calculateSimilarity(normalizedCurrent, normalizedPrevious);
  return similarity > 0.95;
}

/**
 * Calculate similarity between two strings (0-1)
 * Uses simple character overlap method
 */
function calculateSimilarity(str1: string, str2: string): number {
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;

  if (longer.length === 0) return 1.0;

  const editDistance = getEditDistance(longer, shorter);
  return (longer.length - editDistance) / longer.length;
}

/**
 * Calculate Levenshtein distance between two strings
 */
function getEditDistance(s1: string, s2: string): number {
  const costs: number[] = [];

  for (let i = 0; i <= s1.length; i++) {
    let lastValue = i;
    for (let j = 0; j <= s2.length; j++) {
      if (i === 0) {
        costs[j] = j;
      } else if (j > 0) {
        let newValue = costs[j - 1];
        if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
          newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
        }
        costs[j - 1] = lastValue;
        lastValue = newValue;
      }
    }
    if (i > 0) costs[s2.length] = lastValue;
  }

  return costs[s2.length];
}
