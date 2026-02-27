import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "react-toastify/dist/ReactToastify.css";
import AppShell from "@/components/AppShell";
import { AuthProvider } from "@/components/AuthProvider";
import { ToastProvider } from "@/components/ToastProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "WINGMAN",
  description: "Your autonomous networking agent",
  openGraph: {
    title: "WINGMAN",
    description: "Your autonomous networking agent",
    siteName: "WINGMAN",
  },
  twitter: {
    card: "summary_large_image",
    title: "WINGMAN",
    description: "Your autonomous networking agent",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-950 text-gray-100`}
      >
        <AuthProvider>
          <AppShell>{children}</AppShell>
          <ToastProvider />
        </AuthProvider>
      </body>
    </html>
  );
}
