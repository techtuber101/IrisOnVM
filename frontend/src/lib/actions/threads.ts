'use server';

export const generateThreadName = async (message: string): Promise<string> => {
  console.log('🎯 [TITLE GENERATION] Starting title generation for message:', {
    messageLength: message.length,
    messagePreview: message.substring(0, 100) + (message.length > 100 ? '...' : ''),
    timestamp: new Date().toISOString()
  });

  try {
    // Default name in case the API fails
    const defaultName =
      message.trim().length > 50
        ? message.trim().substring(0, 47) + '...'
        : message.trim();

    console.log('🔧 [TITLE GENERATION] Default fallback name:', defaultName);

    // OpenAI API key should be stored in an environment variable
    const apiKey = process.env.OPENAI_API_KEY;

    if (!apiKey) {
      console.error('❌ [TITLE GENERATION] OpenAI API key not found in environment variables');
      console.log('🔧 [TITLE GENERATION] Available env vars:', Object.keys(process.env).filter(key => key.includes('API') || key.includes('KEY')));
      return defaultName;
    }

    console.log('✅ [TITLE GENERATION] API key found, length:', apiKey.length);

    const requestBody = {
      model: 'gpt-5-nano',
      messages: [
        {
          role: 'system',
          content:
            "You are a helpful assistant that generates extremely concise titles (2-4 words maximum) for chat threads based on the user's message. Respond with only the title, no other text or punctuation.",
        },
        {
          role: 'user',
          content: `Generate an extremely brief title (2-4 words only) for a chat thread that starts with this message: "${message}"`,
        },
      ],
      max_tokens: 20,
      temperature: 0.7,
    };

    console.log('📤 [TITLE GENERATION] Making API request to OpenAI:', {
      model: requestBody.model,
      messageCount: requestBody.messages.length,
      maxTokens: requestBody.max_tokens,
      temperature: requestBody.temperature,
      url: 'https://api.openai.com/v1/chat/completions'
    });

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(requestBody),
    });

    console.log('📥 [TITLE GENERATION] Received response:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
      headers: Object.fromEntries(response.headers.entries())
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('❌ [TITLE GENERATION] OpenAI API error response:', {
        status: response.status,
        statusText: response.statusText,
        errorData: errorData,
        requestBody: requestBody
      });
      return defaultName;
    }

    const data = await response.json();
    console.log('📊 [TITLE GENERATION] API response data:', {
      hasChoices: !!data.choices,
      choicesLength: data.choices?.length || 0,
      usage: data.usage,
      model: data.model,
      fullResponse: data
    });

    const generatedName = data.choices[0]?.message?.content?.trim();
    console.log('🎉 [TITLE GENERATION] Generated title:', {
      generatedName,
      originalMessage: message.substring(0, 50) + '...',
      success: !!generatedName
    });

    // Return the generated name or default if empty
    const finalName = generatedName || defaultName;
    console.log('✅ [TITLE GENERATION] Final result:', finalName);
    return finalName;
  } catch (error) {
    console.error('💥 [TITLE GENERATION] Unexpected error:', {
      error: error,
      errorMessage: error instanceof Error ? error.message : 'Unknown error',
      errorStack: error instanceof Error ? error.stack : undefined,
      message: message.substring(0, 50) + '...'
    });
    // Fall back to using a truncated version of the message
    const fallbackName = message.trim().length > 50
      ? message.trim().substring(0, 47) + '...'
      : message.trim();
    console.log('🔧 [TITLE GENERATION] Using fallback name:', fallbackName);
    return fallbackName;
  }
};
