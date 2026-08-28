import dataset from '../data/cards.json';

export type KnowledgeCard = {
  id: string; slug: string; domain: string; sourceName: string; sourceGroup: string;
  originalTitle: string; title: string; description: string; summary: string;
  keyPoints: string[]; whyItMatters: string; limitations: string; originalUrl: string;
  publishedAt: string; retrievedAt: string; tags: string[]; score: number;
  aiGenerated: boolean; discoveredBy: string[];
};

export type CardDataset = {
  generatedAt: string; timezone: string; edition: string; cards: KnowledgeCard[];
  sourceErrors: Record<string, string>;
};

const fallbackDataset = dataset as CardDataset;
const remoteDatasetUrl = process.env.CARD_DATA_URL ?? 'https://raw.githubusercontent.com/Jerome-Jiayu-Lin/Quant-newsletter/main/web/data/cards.json';

export async function getDataset(): Promise<CardDataset> {
  try {
    const response = await fetch(remoteDatasetUrl, {
      cache: 'no-store',
      signal: AbortSignal.timeout(4000),
    });
    if (response.ok) return (await response.json()) as CardDataset;
  } catch {
    // Local builds and first deploys use the bundled edition until main has data.
  }
  return fallbackDataset;
}

export async function getCard(slug: string): Promise<KnowledgeCard | undefined> {
  const current = await getDataset();
  return current.cards.find((card) => card.slug === slug);
}
export function formatSingaporeTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Singapore', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value));
}
