'use client';

import { createMutationHook } from '@/hooks/use-query';
import { 
  createThread, 
  addUserMessage 
} from '@/lib/api';
import { toast } from 'sonner';

export const useCreateThread = createMutationHook(
  ({ projectId }: { projectId: string }) => createThread(projectId),
  {
    onSuccess: () => {
      toast.success('Thread created successfully');
    },
    errorContext: {
      operation: 'create thread',
      resource: 'thread'
    }
  }
);

export const useAddUserMessage = createMutationHook(
  ({
    threadId,
    content,
    metadata,
    isLLMMessage,
    type,
  }: {
    threadId: string;
    content: string;
    metadata?: Record<string, unknown>;
    isLLMMessage?: boolean;
    type?: string;
  }) =>
    addUserMessage(threadId, content, {
      metadata,
      isLLMMessage,
      type,
    }),
  {
    errorContext: {
      operation: 'add message',
      resource: 'message',
    },
  },
);
