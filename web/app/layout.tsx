import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? 'https://jeromebrief.com'),
  title: 'Jerome Brief · 研究者的每日信号',
  description: '每日精选量化研究、AI 工程与高价值工具，生成可追溯的双语知识卡。',
  openGraph: { siteName: 'Jerome Brief', images: [{ url: '/og.webp', width: 1200, height: 675, alt: 'Jerome Brief daily research signals' }] },
  twitter: { card: 'summary_large_image', images: ['/og.webp'] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
