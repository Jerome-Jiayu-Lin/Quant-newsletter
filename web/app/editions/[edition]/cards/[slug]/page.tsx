import CardDetailPage from '../../../../components/card-detail-page';

type PageProps = { params: Promise<{ edition: string; slug: string }> };

export default async function HistoricalCardPage({ params }: PageProps) {
  const { edition, slug } = await params;
  return <CardDetailPage edition={edition} locale="zh" slug={slug} />;
}
