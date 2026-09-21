import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = { title: 'SmartLab OS · Control Center', description: 'Windows lab observability and operations' }

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>
}

