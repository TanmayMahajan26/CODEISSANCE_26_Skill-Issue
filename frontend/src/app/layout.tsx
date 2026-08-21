import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { MainLayout } from "@/components/layout/MainLayout";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Kovi - Financial Customer 360",
  description: "Next-Best-Opportunity Engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} antialiased`}>
      <body className="min-h-screen flex flex-col font-sans bg-[#EAEAEA]">
        <Providers>
          <MainLayout>{children}</MainLayout>
        </Providers>
      </body>
    </html>
  );
}
