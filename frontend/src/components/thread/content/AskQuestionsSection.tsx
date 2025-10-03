'use client';

import React from 'react';
import { MessageCircleQuestion } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AskQuestionsSectionProps {
  questions: string[];
  className?: string;
}

export const AskQuestionsSection: React.FC<AskQuestionsSectionProps> = ({
  questions,
  className
}) => {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className={cn("w-full max-w-3xl mt-4", className)}>
      {/* Divider Line */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-zinc-200 dark:border-zinc-700" />
        </div>
      </div>

      {/* Questions Section */}
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2">
          <MessageCircleQuestion className="h-5 w-5 text-blue-500 dark:text-blue-400" />
          <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            Additional Questions & Smart Suggestions:
          </h3>
        </div>

        {/* Questions List */}
        <ol className="space-y-2 pl-6">
          {questions.map((question, index) => (
            <li 
              key={index}
              className="text-sm text-zinc-600 dark:text-zinc-400 list-decimal"
            >
              {question}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
};

