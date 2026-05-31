import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FB to Medium Copier',
  description: 'Browse Facebook posts and copy content to Medium',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
