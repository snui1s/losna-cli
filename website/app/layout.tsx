import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Losna CLI 🌒 | Deep AI Terminal Assistant & Security Auditing',
  description: 'An all-around, deep AI terminal assistant built for deep code comprehension, architecture inspection, vulnerability detection, and true BYOK freedom.',
  keywords: ['AI Terminal', 'CLI', 'Security Audit', 'OpenRouter', 'BYOK', 'DeepSeek', 'Claude', 'Code Review'],
  icons: {
    icon: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext x='50%25' y='52%25' text-anchor='middle' dominant-baseline='central' font-size='75'%3E🌒%3C/text%3E%3C/svg%3E`,
  },
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
