'use client';

import { useSubscriptionData } from '@/contexts/SubscriptionContext';
import { useEffect, useMemo } from 'react';
import { isLocalMode } from '@/lib/config';
import { useAvailableModels } from '@/hooks/react-query/subscriptions/use-model';
import {
  useModelStore,
  canAccessModel,
  formatModelName,
  getPrefixedModelId,
  type SubscriptionStatus,
  type ModelOption,
  type CustomModel
} from '@/lib/stores/model-store';

export const useModelSelection = () => {
  const { data: subscriptionData } = useSubscriptionData();
  const { data: modelsData, isLoading: isLoadingModels } = useAvailableModels({
    refetchOnMount: false,
  });
  
  const {
    selectedModel,
    customModels,
    hasHydrated,
    setSelectedModel,
    addCustomModel,
    updateCustomModel,
    removeCustomModel,
    setCustomModels,
    setHasHydrated,
    getDefaultModel,
    resetToDefault,
  } = useModelStore();
  
  const subscriptionStatus: SubscriptionStatus = (subscriptionData?.subscription?.status === 'active' || subscriptionData?.subscription?.status === 'trialing')
    ? 'active' 
    : 'no_subscription';

  useEffect(() => {
    if (isLocalMode() && hasHydrated && typeof window !== 'undefined') {
      try {
        const storedModels = localStorage.getItem('customModels');
        if (storedModels) {
          const parsedModels = JSON.parse(storedModels);
          if (Array.isArray(parsedModels)) {
            const validModels = parsedModels.filter((model: any) => 
              model && typeof model === 'object' && 
              typeof model.id === 'string' && 
              typeof model.label === 'string'
            );
            setCustomModels(validModels);
          }
        }
      } catch (e) {
        console.error('Error loading custom models:', e);
      }
    }
  }, [isLocalMode, hasHydrated, setCustomModels]);

  const MODEL_OPTIONS = useMemo(() => {
    let models: ModelOption[] = [];
    if (!modelsData?.models || isLoadingModels) {
      models = [
        { 
          id: 'gemini-2.5-flash', 
          label: 'Gemini 2.5 Flash', 
          requiresSubscription: false,
          priority: 100,
          recommended: true,
          top: true,
          capabilities: ['chat', 'function_calling', 'vision', 'structured_output'],
          contextWindow: 1000000
        },
        { 
          id: 'gemini-2.5-flash-lite', 
          label: 'Gemini 2.5 Flash Lite', 
          requiresSubscription: false,
          priority: 90,
          recommended: false,
          top: true,
          capabilities: ['chat', 'function_calling', 'vision', 'structured_output'],
          contextWindow: 1000000
        },
        { 
          id: 'gpt-5-mini', 
          label: 'GPT-5 Mini', 
          requiresSubscription: false,
          priority: 85,
          recommended: false,
          top: true,
          capabilities: ['chat', 'function_calling', 'structured_output'],
          contextWindow: 400000
        },
        { 
          id: 'gpt-5', 
          label: 'GPT-5', 
          requiresSubscription: false,
          priority: 80,
          recommended: false,
          top: true,
          capabilities: ['chat', 'function_calling', 'structured_output'],
          contextWindow: 400000
        }
      ];
    } else {
      // Show only the 4 specified models from API data
      const geminiFlashModel = modelsData.models.find(model => 
        model.short_name === 'gemini-2.5-flash' || 
        model.id === 'gemini/gemini-2.5-flash' ||
        model.display_name === 'Gemini 2.5 Flash'
      );
      
      const geminiLiteModel = modelsData.models.find(model => 
        model.short_name === 'gemini-2.5-flash-lite' || 
        model.id === 'gemini/gemini-2.5-flash-lite' ||
        model.display_name === 'Gemini 2.5 Flash Lite'
      );
      
      const gpt5Model = modelsData.models.find(model => 
        model.short_name === 'gpt-5' || 
        model.id === 'openai/gpt-5' ||
        model.display_name === 'GPT-5'
      );
      
      const gpt5MiniModel = modelsData.models.find(model => 
        model.short_name === 'gpt-5-mini' || 
        model.id === 'openai/gpt-5-mini' ||
        model.display_name === 'GPT-5 Mini'
      );
      
      models = [];
      
      if (geminiFlashModel) {
        models.push({
          id: geminiFlashModel.short_name || 'gemini-2.5-flash',
          label: geminiFlashModel.display_name || 'Gemini 2.5 Flash',
          requiresSubscription: geminiFlashModel.requires_subscription || false,
          priority: geminiFlashModel.priority || 100,
          recommended: geminiFlashModel.recommended || true,
          top: true,
          capabilities: geminiFlashModel.capabilities || [],
          contextWindow: geminiFlashModel.context_window || 1000000
        });
      } else {
        // Fallback if Gemini Flash model not found in API
        models.push({
          id: 'gemini-2.5-flash',
          label: 'Gemini 2.5 Flash',
          requiresSubscription: false,
          priority: 100,
          recommended: true,
          top: true,
          capabilities: ['chat', 'function_calling', 'vision', 'structured_output'],
          contextWindow: 1000000
        });
      }
      
      if (geminiLiteModel) {
        models.push({
          id: geminiLiteModel.short_name || 'gemini-2.5-flash-lite',
          label: geminiLiteModel.display_name || 'Gemini 2.5 Flash Lite',
          requiresSubscription: geminiLiteModel.requires_subscription || false,
          priority: geminiLiteModel.priority || 90,
          recommended: geminiLiteModel.recommended || false,
          top: true,
          capabilities: geminiLiteModel.capabilities || [],
          contextWindow: geminiLiteModel.context_window || 1000000
        });
      } else {
        // Fallback if Gemini Lite model not found in API
        models.push({
          id: 'gemini-2.5-flash-lite',
          label: 'Gemini 2.5 Flash Lite',
          requiresSubscription: false,
          priority: 90,
          recommended: false,
          top: true,
          capabilities: ['chat', 'function_calling', 'vision', 'structured_output'],
          contextWindow: 1000000
        });
      }
      
      if (gpt5MiniModel) {
        models.push({
          id: gpt5MiniModel.short_name || 'gpt-5-mini',
          label: gpt5MiniModel.display_name || 'GPT-5 Mini',
          requiresSubscription: gpt5MiniModel.requires_subscription || false,
          priority: gpt5MiniModel.priority || 85,
          recommended: gpt5MiniModel.recommended || false,
          top: true,
          capabilities: gpt5MiniModel.capabilities || [],
          contextWindow: gpt5MiniModel.context_window || 400000
        });
      } else {
        // Fallback if GPT-5 Mini model not found in API
        models.push({
          id: 'gpt-5-mini',
          label: 'GPT-5 Mini',
          requiresSubscription: false,
          priority: 85,
          recommended: false,
          top: true,
          capabilities: ['chat', 'function_calling', 'structured_output'],
          contextWindow: 400000
        });
      }
      
      if (gpt5Model) {
        models.push({
          id: gpt5Model.short_name || 'gpt-5',
          label: gpt5Model.display_name || 'GPT-5',
          requiresSubscription: gpt5Model.requires_subscription || false,
          priority: gpt5Model.priority || 80,
          recommended: gpt5Model.recommended || false,
          top: true,
          capabilities: gpt5Model.capabilities || [],
          contextWindow: gpt5Model.context_window || 400000
        });
      } else {
        // Fallback if GPT-5 model not found in API
        models.push({
          id: 'gpt-5',
          label: 'GPT-5',
          requiresSubscription: false,
          priority: 80,
          recommended: false,
          top: true,
          capabilities: ['chat', 'function_calling', 'structured_output'],
          contextWindow: 400000
        });
      }
    }
    
    if (isLocalMode() && customModels.length > 0) {
      const customModelOptions = customModels.map(model => ({
        id: model.id,
        label: model.label || formatModelName(model.id),
        requiresSubscription: false,
        top: false,
        isCustom: true,
        priority: 30,
      }));
      
      models = [...models, ...customModelOptions];
    }
    
    const sortedModels = models.sort((a, b) => {
      if (a.recommended !== b.recommended) {
        return a.recommended ? -1 : 1;
      }

      if (a.priority !== b.priority) {
        return (b.priority || 0) - (a.priority || 0);
      }
      
      return a.label.localeCompare(b.label);
    });
    
    return sortedModels;
  }, [modelsData, isLoadingModels, customModels]);

  const availableModels = useMemo(() => {
    return isLocalMode() 
      ? MODEL_OPTIONS 
      : MODEL_OPTIONS.filter(model => 
          canAccessModel(subscriptionStatus, model.requiresSubscription)
        );
  }, [MODEL_OPTIONS, subscriptionStatus]);

  useEffect(() => {
    if (!hasHydrated || isLoadingModels || typeof window === 'undefined') {
      return;
    }
    
    const isValidModel = MODEL_OPTIONS.some(model => model.id === selectedModel) ||
                        (isLocalMode() && customModels.some(model => model.id === selectedModel));
    
    if (!isValidModel) {
      console.log('🔧 ModelSelection: Invalid model detected, resetting to default');
      resetToDefault(subscriptionStatus);
      return;
    }
    
    if (!isLocalMode()) {
      const modelOption = MODEL_OPTIONS.find(m => m.id === selectedModel);
      if (modelOption && !canAccessModel(subscriptionStatus, modelOption.requiresSubscription)) {
        console.log('🔧 ModelSelection: User lost access to model, resetting to default');
        resetToDefault(subscriptionStatus);
      }
    }
  }, [hasHydrated, selectedModel, subscriptionStatus, MODEL_OPTIONS, customModels, isLoadingModels, resetToDefault]);

  const handleModelChange = (modelId: string) => {
    const isCustomModel = isLocalMode() && customModels.some(model => model.id === modelId);
    
    const modelOption = MODEL_OPTIONS.find(option => option.id === modelId);
    
    if (!modelOption && !isCustomModel) {
      resetToDefault(subscriptionStatus);
      return;
    }

    if (!isCustomModel && !isLocalMode() && 
        !canAccessModel(subscriptionStatus, modelOption?.requiresSubscription ?? false)) {
      return;
    }
    
    setSelectedModel(modelId);
  };

  const getActualModelId = (modelId: string): string => {
    const isCustomModel = isLocalMode() && customModels.some(model => model.id === modelId);
    return isCustomModel ? getPrefixedModelId(modelId, true) : modelId;
  };

  const refreshCustomModels = () => {
    if (isLocalMode() && typeof window !== 'undefined') {
      try {
        const storedModels = localStorage.getItem('customModels');
        if (storedModels) {
          const parsedModels = JSON.parse(storedModels);
          if (Array.isArray(parsedModels)) {
            const validModels = parsedModels.filter((model: any) => 
              model && typeof model === 'object' && 
              typeof model.id === 'string' && 
              typeof model.label === 'string'
            );
            setCustomModels(validModels);
          }
        }
      } catch (e) {
        console.error('Error loading custom models:', e);
      }
    }
  };

  return {
    selectedModel,
    handleModelChange,
    setSelectedModel: handleModelChange,
    availableModels,
    allModels: MODEL_OPTIONS,
    customModels,
    addCustomModel,
    updateCustomModel,
    removeCustomModel,
    refreshCustomModels,
    getActualModelId,
    canAccessModel: (modelId: string) => {
      if (isLocalMode()) return true;
      const model = MODEL_OPTIONS.find(m => m.id === modelId);
      return model ? canAccessModel(subscriptionStatus, model.requiresSubscription) : false;
    },
    isSubscriptionRequired: (modelId: string) => {
      return MODEL_OPTIONS.find(m => m.id === modelId)?.requiresSubscription || false;
    },
    subscriptionStatus,
  };
}; 