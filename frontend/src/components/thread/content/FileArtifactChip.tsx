'use client';

import React from 'react';
import { FileText, FileCode, FileImage, File as FileIcon, Table2, FileSpreadsheet } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileArtifactChipProps {
  filePath: string;
  onClick?: (filePath: string) => void;
  className?: string;
}

const getFileIcon = (extension: string) => {
  switch (extension.toLowerCase()) {
    case 'md':
    case 'txt':
    case 'doc':
    case 'docx':
      return FileText;
    case 'js':
    case 'ts':
    case 'tsx':
    case 'jsx':
    case 'py':
    case 'java':
    case 'cpp':
    case 'c':
    case 'html':
    case 'css':
      return FileCode;
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
    case 'webp':
      return FileImage;
    case 'csv':
    case 'tsv':
      return Table2;
    case 'xlsx':
    case 'xls':
      return FileSpreadsheet;
    default:
      return FileIcon;
  }
};

const getFileIconColor = (extension: string) => {
  switch (extension.toLowerCase()) {
    case 'md':
    case 'txt':
      return 'text-blue-500 dark:text-blue-400';
    case 'js':
    case 'ts':
    case 'tsx':
    case 'jsx':
      return 'text-yellow-500 dark:text-yellow-400';
    case 'py':
      return 'text-green-500 dark:text-green-400';
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
    case 'webp':
      return 'text-purple-500 dark:text-purple-400';
    case 'csv':
    case 'xlsx':
    case 'xls':
      return 'text-emerald-500 dark:text-emerald-400';
    default:
      return 'text-zinc-500 dark:text-zinc-400';
  }
};

export const FileArtifactChip: React.FC<FileArtifactChipProps> = ({ 
  filePath, 
  onClick,
  className 
}) => {
  const fileName = filePath.split('/').pop() || filePath;
  const extension = fileName.split('.').pop() || '';
  const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
  
  const Icon = getFileIcon(extension);
  const iconColor = getFileIconColor(extension);

  return (
    <button
      onClick={() => onClick?.(filePath)}
      className={cn(
        "group relative inline-flex items-center gap-2 px-3 py-2 rounded-lg",
        "bg-white/60 dark:bg-zinc-800/60 backdrop-blur-sm",
        "border border-zinc-200/50 dark:border-zinc-700/50",
        "hover:bg-white/80 dark:hover:bg-zinc-800/80",
        "hover:border-zinc-300/80 dark:hover:border-zinc-600/80",
        "hover:shadow-md transition-all duration-200",
        "cursor-pointer",
        className
      )}
    >
      <Icon className={cn("h-4 w-4 flex-shrink-0", iconColor)} />
      <div className="flex flex-col items-start min-w-0">
        <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate max-w-[200px]">
          {nameWithoutExt}
        </span>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          .{extension}
        </span>
      </div>
    </button>
  );
};

