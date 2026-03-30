import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "爬虫智能机器人 - 资讯智能分析系统",
  description: "面向金融资讯智能分析系统的前端工作台：查询分析、每日任务看板、新闻抓取。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="h-full flex overflow-hidden bg-white text-gray-900">
        <Sidebar />
        <main className="flex-1 flex flex-col h-full overflow-hidden bg-white relative">
          {children}
        </main>
      </body>
    </html>
  );
}
