import { createMutationHook, createQueryHook } from "@/hooks/use-query";
import { threadKeys } from "./keys";
import { addUserMessage, getMessages } from "@/lib/api";

export const useMessagesQuery = (threadId: string) =>
  createQueryHook(
    threadKeys.messages(threadId),
    () => getMessages(threadId),
    {
      enabled: !!threadId,
      retry: 1,
      refetchOnMount: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    }
  )();

export const useAddUserMessageMutation = () =>
  createMutationHook(
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
      })
  )();
