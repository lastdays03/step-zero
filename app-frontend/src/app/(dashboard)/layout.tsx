
import React from 'react';
import { Header, MobileNav, Sidebar, SessionExpiredBanner } from "@/features/dashboard/components";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="flex h-screen bg-background">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header />
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-background p-4 md:p-6 pb-32 md:pb-6">
                    <SessionExpiredBanner />
                    {children}
                </main>
            </div>
            <MobileNav />
        </div>
    );
}
