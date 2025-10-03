import { extractToolData, normalizeContentToString } from '../utils';

export interface AskData {
  text: string | null;
  attachments: string[] | null;
  status: string | null;
  success?: boolean;
  timestamp?: string;
}

const parseContent = (content: any): any => {
  if (typeof content === 'string') {
    try {
      return JSON.parse(content);
    } catch (e) {
      return content;
    }
  }
  return content;
};

const extractFromNewFormat = (content: any): { 
  text: string | null;
  attachments: string[] | null;
  status: string | null;
  success?: boolean; 
  timestamp?: string;
} => {
  const parsedContent = parseContent(content);
  
  if (!parsedContent || typeof parsedContent !== 'object') {
    return { text: null, attachments: null, status: null, success: undefined, timestamp: undefined };
  }

  if ('tool_execution' in parsedContent && typeof parsedContent.tool_execution === 'object') {
    const toolExecution = parsedContent.tool_execution;
    const args = toolExecution.arguments || {};
    
    let parsedOutput = toolExecution.result?.output;
    if (typeof parsedOutput === 'string') {
      try {
        parsedOutput = JSON.parse(parsedOutput);
      } catch (e) {
      }
    }

    let attachments: string[] | null = null;
    if (args.attachments) {
      if (typeof args.attachments === 'string') {
        attachments = args.attachments.split(',').map((a: string) => a.trim()).filter((a: string) => a.length > 0);
      } else if (Array.isArray(args.attachments)) {
        attachments = args.attachments;
      }
    }

    let status: string | null = null;
    if (parsedOutput && typeof parsedOutput === 'object' && parsedOutput.status) {
      status = parsedOutput.status;
    }

    const extractedData = {
      text: args.text || null,
      attachments,
      status: status || parsedContent.summary || null,
      success: toolExecution.result?.success,
      timestamp: toolExecution.execution_details?.timestamp
    };
    
    return extractedData;
  }

  if ('role' in parsedContent && 'content' in parsedContent) {
    return extractFromNewFormat(parsedContent.content);
  }

  return { text: null, attachments: null, status: null, success: undefined, timestamp: undefined };
};

const extractFromLegacyFormat = (content: any): { 
  text: string | null;
  attachments: string[] | null;
  status: string | null;
} => {
  const toolData = extractToolData(content);
  
  if (toolData.toolResult && toolData.arguments) {
    let attachments: string[] | null = null;
    if (toolData.arguments.attachments) {
      if (Array.isArray(toolData.arguments.attachments)) {
        attachments = toolData.arguments.attachments;
      } else if (typeof toolData.arguments.attachments === 'string') {
        attachments = toolData.arguments.attachments.split(',').map(a => a.trim()).filter(a => a.length > 0);
      }
    }
    
    return {
      text: toolData.arguments.text || null,
      attachments,
      status: null
    };
  }

  const contentStr = normalizeContentToString(content);
  if (!contentStr) {
    return { text: null, attachments: null, status: null };
  }

  let attachments: string[] | null = null;
  const attachmentsMatch = contentStr.match(/attachments=["']([^"']*)["']/i);
  if (attachmentsMatch) {
    attachments = attachmentsMatch[1].split(',').map(a => a.trim()).filter(a => a.length > 0);
  }

  let text: string | null = null;
  const textMatch = contentStr.match(/<ask[^>]*>([^<]*)<\/ask>/i);
  if (textMatch) {
    text = textMatch[1].trim();
  }
  
  return {
    text,
    attachments,
    status: null
  };
};

export function extractAskData(
  assistantContent: any,
  toolContent: any,
  isSuccess: boolean,
  toolTimestamp?: string,
  assistantTimestamp?: string
): {
  text: string | null;
  attachments: string[] | null;
  status: string | null;
  actualIsSuccess: boolean;
  actualToolTimestamp?: string;
  actualAssistantTimestamp?: string;
} {
  let text: string | null = null;
  let attachments: string[] | null = null;
  let status: string | null = null;
  let actualIsSuccess = isSuccess;
  let actualToolTimestamp = toolTimestamp;
  let actualAssistantTimestamp = assistantTimestamp;

  const assistantNewFormat = extractFromNewFormat(assistantContent);
  const toolNewFormat = extractFromNewFormat(toolContent);

  if (assistantNewFormat.text || assistantNewFormat.attachments || assistantNewFormat.status) {
    text = assistantNewFormat.text;
    attachments = assistantNewFormat.attachments;
    status = assistantNewFormat.status;
    if (assistantNewFormat.success !== undefined) {
      actualIsSuccess = assistantNewFormat.success;
    }
    if (assistantNewFormat.timestamp) {
      actualAssistantTimestamp = assistantNewFormat.timestamp;
    }
  } else if (toolNewFormat.text || toolNewFormat.attachments || toolNewFormat.status) {
    text = toolNewFormat.text;
    attachments = toolNewFormat.attachments;
    status = toolNewFormat.status;
    if (toolNewFormat.success !== undefined) {
      actualIsSuccess = toolNewFormat.success;
    }
    if (toolNewFormat.timestamp) {
      actualToolTimestamp = toolNewFormat.timestamp;
    }
  } else {
    const assistantLegacy = extractFromLegacyFormat(assistantContent);
    const toolLegacy = extractFromLegacyFormat(toolContent);

    text = assistantLegacy.text || toolLegacy.text;
    attachments = assistantLegacy.attachments || toolLegacy.attachments;
    status = assistantLegacy.status || toolLegacy.status;
  }
  
  return {
    text,
    attachments,
    status,
    actualIsSuccess,
    actualToolTimestamp,
    actualAssistantTimestamp
  };
}

// Parse questions from ask tool text
export function parseAskQuestions(text: string | null): string[] {
  if (!text) {
    return [];
  }

  const questions: string[] = [];

  // Look for numbered questions like "1. Question?" or "1) Question?"
  const numberedMatches = text.match(/^\s*\d+[\.)]\s+(.+)$/gm);
  if (numberedMatches && numberedMatches.length > 0) {
    numberedMatches.forEach(match => {
      const cleaned = match.replace(/^\s*\d+[\.)]\s+/, '').trim();
      if (cleaned) {
        questions.push(cleaned);
      }
    });
  }

  // If no numbered questions found, look for bullet points
  if (questions.length === 0) {
    const bulletMatches = text.match(/^\s*[-•*]\s+(.+)$/gm);
    if (bulletMatches && bulletMatches.length > 0) {
      bulletMatches.forEach(match => {
        const cleaned = match.replace(/^\s*[-•*]\s+/, '').trim();
        if (cleaned) {
          questions.push(cleaned);
        }
      });
    }
  }

  // If still no questions found, split by newlines and filter question-like lines
  if (questions.length === 0) {
    const lines = text.split('\n').filter(line => line.trim().length > 0);
    lines.forEach(line => {
      const trimmed = line.trim();
      // Check if line ends with question mark or contains "you want" or "would you"
      if (trimmed.endsWith('?') || /(?:do you|would you|can you|should|want to)/i.test(trimmed)) {
        questions.push(trimmed);
      }
    });
  }

  return questions;
} 