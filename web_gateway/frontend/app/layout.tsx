import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'ROS2 Web Gateway',
  description: 'A focused experiment console for ROS2.',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
