import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? 'http://localhost:3000'),
  title: 'Quant Brief · 研究者的每日信号',
  description: '每日精选量化研究、AI 工程与高价值工具，生成可追溯的中文知识卡。',
  openGraph: {
    title: 'Quant Brief · 研究者的每日信号',
    description: '每日精选量化研究、AI 工程与高价值工具，生成可追溯的中文知识卡。',
    images: [{ url: '/og.webp', width: 1200, height: 675, alt: 'Quant Brief · 研究者的每日信号' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Quant Brief · 研究者的每日信号',
    description: '每日精选量化研究、AI 工程与高价值工具，生成可追溯的中文知识卡。',
    images: ['/og.webp'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
