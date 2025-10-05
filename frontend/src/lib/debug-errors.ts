// Global error handler for unhandled errors
export function setupGlobalErrorHandlers() {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.group('🚨 Unhandled Promise Rejection');
    console.error('Reason:', event.reason);
    console.error('Promise:', event.promise);
    console.groupEnd();
    
    // Prevent the default handler (which logs to console)
    event.preventDefault();
  });

  // Handle uncaught errors
  window.addEventListener('error', (event) => {
    console.group('🚨 Uncaught Error');
    console.error('Message:', event.message);
    console.error('Source:', event.filename);
    console.error('Line:', event.lineno);
    console.error('Column:', event.colno);
    console.error('Error:', event.error);
    console.groupEnd();
  });

  // Handle console errors (override console.error for better formatting)
  const originalConsoleError = console.error;
  console.error = (...args) => {
    console.group('🔴 Console Error');
    args.forEach((arg, index) => {
      if (arg instanceof Error) {
        console.error(`Error ${index + 1}:`, arg.message);
        console.error(`Stack:`, arg.stack);
      } else {
        console.error(`Arg ${index + 1}:`, arg);
      }
    });
    console.groupEnd();
    
    // Call original console.error
    originalConsoleError.apply(console, args);
  };
}

// Debug helper function
export function debugError(error: any, context?: string) {
  console.group(`🐛 Debug Error${context ? ` - ${context}` : ''}`);
  console.error('Error:', error);
  console.error('Type:', typeof error);
  console.error('Constructor:', error?.constructor?.name);
  
  if (error instanceof Error) {
    console.error('Message:', error.message);
    console.error('Stack:', error.stack);
  }
  
  if (error && typeof error === 'object') {
    console.error('Keys:', Object.keys(error));
    console.error('Stringified:', JSON.stringify(error, null, 2));
  }
  
  console.groupEnd();
}
