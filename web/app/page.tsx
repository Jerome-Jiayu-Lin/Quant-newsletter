import type { Metadata } from 'next';
import HomePage from './components/home-page';

export const metadata: Metadata = {
  alternates: { canonical: '/', languages: { 'zh-CN': '/', en: '/en' } },
};

export default function Home() { return <HomePage locale="zh" />; }
