
import React from 'react';
import { Sidebar } from "@/features/dashboard/components/Sidebar";
import { Header } from "@/features/dashboard/components/Header";
import { MobileNav } from "@/features/dashboard/components/MobileNav";

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
                    {children}
                </main>
            </div>
            <MobileNav />
        </div>
    );
}
