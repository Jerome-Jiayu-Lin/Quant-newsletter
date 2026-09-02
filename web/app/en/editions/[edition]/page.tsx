import { notFound } from 'next/navigation';
import EditionUnavailablePage from '../../../components/edition-unavailable-page';
import HomePage from '../../../components/home-page';
import type { CardDataset } from '../../../../lib/cards';
import { EditionNotFoundError, EditionUnavailableError, getHistoricalDataset } from '../../../../lib/cards';

type PageProps = { params: Promise<{ edition: string }> };

export default async function EnglishHistoricalEditionPage({ params }: PageProps) {
  const { edition } = await params;
  let dataset: CardDataset;
  try {
    dataset = await getHistoricalDataset(edition);
  } catch (error) {
    if (error instanceof EditionNotFoundError) notFound();
    if (error instanceof EditionUnavailableError) return <EditionUnavailablePage edition={edition} locale="en" />;
    throw error;
  }
  return <HomePage editionDate={edition} initialDataset={dataset} locale="en" />;
}
