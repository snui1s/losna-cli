import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Losna CLI 🌒 | Deep AI Terminal Assistant & Security Auditing',
  description: 'An all-around, deep AI terminal assistant built for deep code comprehension, architecture inspection, vulnerability detection, and true BYOK freedom.',
  keywords: ['AI Terminal', 'CLI', 'Security Audit', 'OpenRouter', 'BYOK', 'DeepSeek', 'Claude', 'Code Review'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
