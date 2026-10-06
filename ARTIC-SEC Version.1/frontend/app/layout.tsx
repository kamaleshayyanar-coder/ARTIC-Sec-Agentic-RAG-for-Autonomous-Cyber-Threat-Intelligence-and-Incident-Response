import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { Footer } from "@/components/layout/Footer";
import { ToastProvider } from "@/components/ui/toast";

export const metadata: Metadata = {
  title: "ARTIC-Sec | Autonomous SOC & Threat Intelligence",
  description:
    "Industrial-Standard Real-Time Intelligent Cybersecurity Platform with LangGraph Agentic AI, RAG & ML Threat Classification",
  icons: {
    icon: "/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-night-950 text-slate-100 antialiased selection:bg-sky-500/30 selection:text-sky-200">
        <ToastProvider>
          <div className="flex h-screen w-screen flex-col overflow-hidden">
            <Header />
            <div className="flex flex-1 overflow-hidden">
              <Sidebar />
              <main className="flex-1 overflow-y-auto p-6 bg-night-950/40">
                {children}
              </main>
            </div>
            <Footer />
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}
