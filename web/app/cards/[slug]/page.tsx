import type { Metadata } from 'next';
import CardDetailPage from '../../components/card-detail-page';
import { getCard } from '../../../lib/cards';

type PageProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const card = await getCard((await params).slug);
  if (!card) return {};
  return { title: `${card.title} · Jerome Brief`, description: card.description, alternates: { canonical: `/cards/${card.slug}`, languages: { 'zh-CN': `/cards/${card.slug}`, en: `/en/cards/${card.slug}` } }, openGraph: { title: card.title, description: card.description, images: [] }, twitter: { card: 'summary', title: card.title, description: card.description, images: [] } };
}

export default async function CardPage({ params }: PageProps) { return <CardDetailPage locale="zh" slug={(await params).slug} />; }
