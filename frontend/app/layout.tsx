import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Irrigation Control System',
  description: 'Monitor and control your irrigation system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-primary-600 text-white shadow-md">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold">Irrigation Control System</h1>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="bg-gray-100 border-t border-gray-200 mt-auto">
            <div className="container mx-auto px-4 py-4 text-center text-gray-500 text-sm">
              &copy; {new Date().getFullYear()} Irrigation Control System
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
} 