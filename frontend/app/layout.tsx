import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'sonner'
import Link from 'next/link'
import { Home, Droplet, Map, LineChart } from 'lucide-react'

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
              <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold">Irrigation Control System</h1>
                <nav className="flex space-x-6">
                  <Link 
                    href="/" 
                    className="flex items-center space-x-2 hover:text-gray-200 transition-colors"
                  >
                    <Home size={20} />
                    <span>Dashboard</span>
                  </Link>
                  <Link 
                    href="/control" 
                    className="flex items-center space-x-2 hover:text-gray-200 transition-colors"
                  >
                    <Droplet size={20} />
                    <span>Control</span>
                  </Link>
                  <Link 
                    href="/zones" 
                    className="flex items-center space-x-2 hover:text-gray-200 transition-colors"
                  >
                    <Map size={20} />
                    <span>Zones</span>
                  </Link>
                  <Link 
                    href="/analytics" 
                    className="flex items-center space-x-2 hover:text-gray-200 transition-colors"
                  >
                    <LineChart size={20} />
                    <span>Analytics</span>
                  </Link>
                </nav>
              </div>
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
        <Toaster />
      </body>
    </html>
  )
} 