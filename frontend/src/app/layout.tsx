import './globals.css'
import type { Metadata } from 'next'
import Navbar from '@/components/Navbar'
import Footer from '@/components/Footer'

export const metadata: Metadata = {
  title: 'Mundi TV - Streaming de Deportes en Vivo',
  description: 'La mejor plataforma para ver partidos de fútbol, NFL, ATP y más en vivo con calidad HD',
  keywords: 'streaming, deportes, fútbol, NFL, ATP, en vivo',
  authors: [{ name: 'Mundi TV' }],
  viewport: 'width=device-width, initial-scale=1.0',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="bg-dark-950 text-gray-100">
        <Navbar />
        <main className="min-h-screen">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  )
}
