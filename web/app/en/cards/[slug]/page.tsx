import type { Metadata } from 'next';
import CardDetailPage from '../../../components/card-detail-page';
import { getCard } from '../../../../lib/cards';

type PageProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const card = await getCard((await params).slug);
  if (!card) return {};
  return {
    title: `${card.titleEn} · Jerome Brief`, description: card.descriptionEn,
    alternates: { canonical: `/en/cards/${card.slug}`, languages: { 'zh-CN': `/cards/${card.slug}`, en: `/en/cards/${card.slug}` } },
    openGraph: { title: card.titleEn, description: card.descriptionEn, images: [] },
    twitter: { card: 'summary', title: card.titleEn, description: card.descriptionEn, images: [] },
  };
}

export default async function EnglishCardPage({ params }: PageProps) {
  return <CardDetailPage locale="en" slug={(await params).slug} />;
}
