import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import RootSharedLayout from '@/app/(root)/shared_layout'
import { polyfillPromiseWithResolvers } from "@/lib/polyfilsResolver";
import { Toaster } from "@/components/ui/toaster"


polyfillPromiseWithResolvers();

import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Quantity Takeoff',
  description: '',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
      <html lang="en">
        <body className={inter.className}>
          <RootSharedLayout>
            {children}
          </RootSharedLayout>
          <Toaster />
        </body>
      </html>
  )
}