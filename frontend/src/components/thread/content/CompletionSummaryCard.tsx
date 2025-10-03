'use client';

import React from 'react';
import { CheckCircle } from 'lucide-react';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';
import { FileArtifactChip } from './FileArtifactChip';

interface CompletionSummaryCardProps {
  context?: string;
  executiveSummary?: string[];
  deliverables?: string[];
  onFileClick?: (filePath: string) => void;
  className?: string;
}

export const CompletionSummaryCard: React.FC<CompletionSummaryCardProps> = ({
  context,
  executiveSummary = [],
  deliverables = [],
  onFileClick,
  className
}) => {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Determine the actual theme
  const currentTheme = theme === 'system' ? systemTheme : theme;
  const logoSrc = currentTheme === 'dark' ? '/irislogowhite.png' : '/irislogo.png';

  return (
    <div className={cn("w-full max-w-3xl", className)}>
      {/* Main Glassy Card */}
      <div className={cn(
        "backdrop-blur-sm bg-gradient-to-br",
        "from-white/80 to-white/60 dark:from-zinc-900/80 dark:to-zinc-800/60",
        "border border-zinc-200/50 dark:border-zinc-700/50",
        "rounded-2xl shadow-lg p-6 space-y-6"
      )}>
        {/* Logo */}
        {mounted && (
          <div className="flex items-start">
            <img 
              src={logoSrc} 
              alt="Iris" 
              className="h-8 object-contain"
              onError={(e) => {
                // Fallback if image fails to load
                e.currentTarget.style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Main Accomplishment Message */}
        <div className="space-y-2">
          <p className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
            I have successfully accomplished executing {context || 'your task'}
          </p>
        </div>

        {/* Executive Summary */}
        {executiveSummary.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
              Executive Summary
            </h3>
            <ul className="space-y-2">
              {executiveSummary.map((point, index) => (
                <li 
                  key={index}
                  className="flex items-start gap-2 text-sm text-zinc-700 dark:text-zinc-300"
                >
                  <span className="text-emerald-500 dark:text-emerald-400 mt-0.5">•</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Key Deliverables */}
        {deliverables.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
              Key Deliverables
            </h3>
            <div className="flex flex-wrap gap-2">
              {deliverables.map((filePath, index) => (
                <FileArtifactChip
                  key={index}
                  filePath={filePath}
                  onClick={onFileClick}
                />
              ))}
            </div>
          </div>
        )}

        {/* Mission Accomplished Footer with Green Tick */}
        <div className="pt-4 border-t border-zinc-200/50 dark:border-zinc-700/50">
          <div className="flex items-center gap-2">
            <div className="relative">
              <CheckCircle className="h-5 w-5 text-emerald-500 dark:text-emerald-400" />
              {/* Subtle glow effect */}
              <div className="absolute inset-0 blur-md bg-emerald-500/30 dark:bg-emerald-400/30 rounded-full" />
            </div>
            <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
              Mission Accomplished
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

