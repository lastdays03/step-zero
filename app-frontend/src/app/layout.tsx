import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { cn } from '@/lib/utils'
import { AuthProvider } from '@/providers/AuthProvider'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { ChatContextProvider, GlobalChatbot } from '@/features/chatbot'
import { Toaster } from '@/components/ui/sonner'

const inter = Inter({ subsets: ['latin'], variable: "--font-sans" })

export const metadata: Metadata = {
    title: 'StepZero - AI Co-Founder',
    description: 'AI-powered co-founder for solopreneurs',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';
    const hasGoogleClientId = googleClientId.trim().length > 0;

    return (
        <html lang="en" suppressHydrationWarning>
            <body className={cn(
                "min-h-screen bg-background font-sans antialiased",
                inter.variable
            )}>
                {hasGoogleClientId ? (
                    <GoogleOAuthProvider clientId={googleClientId}>
                        <AuthProvider>
                            <ChatContextProvider>
                                {children}
                                <GlobalChatbot />
                            </ChatContextProvider>
                            <Toaster />
                        </AuthProvider>
                    </GoogleOAuthProvider>
                ) : (
                    <AuthProvider>
                        <ChatContextProvider>
                            {children}
                            <GlobalChatbot />
                        </ChatContextProvider>
                        <Toaster />
                    </AuthProvider>
                )}
            </body>
        </html>
    )
}
