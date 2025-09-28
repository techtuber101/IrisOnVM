/**
 * Personalized greeting system with 27 pre-prepared greetings
 * Includes time-based greetings and random motivational messages
 */

export interface GreetingOptions {
  firstName?: string;
  includeTimeBased?: boolean;
  includeRandom?: boolean;
}

/**
 * Get the current time of day for time-based greetings
 */
function getTimeOfDay(): 'morning' | 'afternoon' | 'evening' | 'night' {
  const hour = new Date().getHours();
  
  if (hour >= 5 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 22) return 'evening';
  return 'night';
}

/**
 * Extract first name from full name or email
 */
function getFirstName(name?: string, email?: string): string | null {
  if (name) {
    // Extract first name from full name
    const firstName = name.trim().split(' ')[0];
    return firstName || null;
  }
  
  if (email) {
    // Extract name from email prefix
    const emailPrefix = email.split('@')[0];
    // Remove numbers and special characters, capitalize first letter
    const cleanName = emailPrefix.replace(/[0-9._-]/g, '').toLowerCase();
    return cleanName ? cleanName.charAt(0).toUpperCase() + cleanName.slice(1) : null;
  }
  
  return null;
}

/**
 * Time-based greetings
 */
const timeBasedGreetings = {
  morning: [
    'Good morning',
    'Rise and shine',
    'Morning',
    'Good morning, ready to start?',
    'Morning, what shall we tackle today?'
  ],
  afternoon: [
    'Good afternoon',
    'Afternoon',
    'Good afternoon, how can I help?',
    'Afternoon, what\'s on your agenda?',
    'Good afternoon, ready to continue?'
  ],
  evening: [
    'Good evening',
    'Evening',
    'Good evening, how can I help you?',
    'Evening, what shall we do today?',
    'Good evening, ready to work?'
  ],
  night: [
    'Good evening', // Using evening for night to be more polite
    'Evening',
    'Good evening, how can I help you?',
    'Evening, what shall we do today?',
    'Good evening, ready to work?'
  ]
};

/**
 * Random motivational and casual greetings
 */
const randomGreetings = [
  'Ready when you are.',
  'I\'m ready, are you?',
  'Let\'s build something great.',
  'Tell me and I\'ll get it done.',
  'What would you like to do today?',
  'How can I assist you today?',
  'What\'s on your mind?',
  'Ready to create something amazing?',
  'Let\'s make things happen.',
  'What shall we work on?',
  'I\'m here to help.',
  'What can I do for you?',
  'Let\'s get started.',
  'Ready to dive in?',
  'What\'s the plan?',
  'Let\'s tackle this together.',
  'How can I make your day better?',
  'What would you like to accomplish?',
  'Ready to solve some problems?',
  'Let\'s create something wonderful.',
  'What\'s your next move?',
  'I\'m all ears.',
  'Let\'s make progress.',
  'What\'s the challenge?',
  'Ready to innovate?',
  'Let\'s turn ideas into reality.',
  'What shall we create today?'
];

/**
 * Generate a personalized greeting
 */
export function generateGreeting(options: GreetingOptions = {}): string {
  const { firstName, includeTimeBased = true, includeRandom = true } = options;
  
  // If we have a first name, use it
  const name = firstName || null;
  
  // Decide whether to use time-based or random greeting
  const useTimeBased = includeTimeBased && Math.random() < 0.4; // 40% chance for time-based
  const useRandom = includeRandom && !useTimeBased;
  
  if (useTimeBased) {
    const timeOfDay = getTimeOfDay();
    const timeGreetings = timeBasedGreetings[timeOfDay];
    const randomTimeGreeting = timeGreetings[Math.floor(Math.random() * timeGreetings.length)];
    
    if (name) {
      return `${randomTimeGreeting}, ${name}`;
    }
    return randomTimeGreeting;
  }
  
  if (useRandom) {
    const randomGreeting = randomGreetings[Math.floor(Math.random() * randomGreetings.length)];
    
    if (name && randomGreeting.includes('?')) {
      // For questions, add the name at the beginning
      return `${name}, ${randomGreeting.toLowerCase()}`;
    } else if (name && !randomGreeting.includes('?')) {
      // For statements, add the name at the end
      return `${randomGreeting}, ${name}`;
    }
    
    return randomGreeting;
  }
  
  // Fallback
  if (name) {
    return `Hello, ${name}. What would you like to do today?`;
  }
  
  return 'What would you like to do today?';
}

/**
 * Get a greeting for a user with their profile information
 */
export function getUserGreeting(user: { user_metadata?: { name?: string }; email?: string } | null): string {
  if (!user) {
    return 'What would you like to do today?';
  }
  
  const firstName = getFirstName(user.user_metadata?.name, user.email);
  
  return generateGreeting({
    firstName: firstName || undefined,
    includeTimeBased: true,
    includeRandom: true
  });
}

/**
 * Get all available greetings for testing or display purposes
 */
export function getAllGreetings(): string[] {
  const allGreetings: string[] = [];
  
  // Add time-based greetings
  Object.values(timeBasedGreetings).forEach(greetings => {
    allGreetings.push(...greetings);
  });
  
  // Add random greetings
  allGreetings.push(...randomGreetings);
  
  return allGreetings;
}
