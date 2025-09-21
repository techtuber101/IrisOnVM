'use server';

export const generateThreadName = async (message: string): Promise<string> => {
  try {
    // Default name in case the API fails
    const defaultName =
      message.trim().length > 50
        ? message.trim().substring(0, 47) + '...'
        : message.trim();

    // Call the backend API endpoint
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/threads/generate-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Backend API error:', errorData);
      return defaultName;
    }

    const data = await response.json();
    const generatedName = data.title?.trim();

    // Return the generated name or default if empty
    return generatedName || defaultName;
  } catch (error) {
    console.error('Error generating thread name:', error);
    // Fall back to using a truncated version of the message
    return message.trim().length > 50
      ? message.trim().substring(0, 47) + '...'
      : message.trim();
  }
};
