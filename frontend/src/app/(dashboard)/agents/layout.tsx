import { Metadata } from 'next';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Agent Conversation | Iris',
  description: 'Interactive agent conversation powered by Iris',
  openGraph: {
    title: 'Agent Conversation | Iris',
    description: 'Interactive agent conversation powered by Iris',
    type: 'website',
  },
};

export default async function AgentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
