import type { Metadata } from 'next';
import HomePage from '../components/home-page';

export const metadata: Metadata = {
  title: "Jerome Brief · Daily research signals",
  description: 'Curated quantitative research, AI engineering, and high-value tools in traceable English knowledge cards.',
  alternates: { canonical: '/en', languages: { 'zh-CN': '/', en: '/en' } },
};

export default function EnglishHome() { return <HomePage locale="en" />; }
