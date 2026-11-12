import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
  title: 'REDRAFT — The NFL Draft Time Machine',
  description: 'Draft the past. Rewrite the future. An evidence-led historical NFL draft research game.',
  manifest: '/manifest.webmanifest',
  icons: { icon: '/favicon.svg' },
  appleWebApp: { capable: true, title: 'REDRAFT', statusBarStyle: 'default' },
};
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
