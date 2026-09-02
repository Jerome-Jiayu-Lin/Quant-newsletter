import dataset from '../data/cards.json' with { type: 'json' };

export type KnowledgeCard = {
  id: string; slug: string; domain: string; contentType?: 'repository' | 'paper' | 'article' | 'video'; sourceName: string; sourceGroup: string;
  originalTitle: string; title: string; description: string; summary: string;
  keyPoints: string[]; whyItMatters: string; limitations: string; originalUrl: string;
  titleEn: string; descriptionEn: string; summaryEn: string;
  keyPointsEn: string[]; whyItMattersEn: string; limitationsEn: string;
  publishedAt: string; retrievedAt: string; tags: string[]; score: number;
  tagsEn?: string[]; features?: Array<{ id: string; label: { zh: string; en: string } }>;
  aiGenerated: boolean; summaryProvider: string; summaryModel?: string | null; discoveredBy: string[];
};

export type CardDataset = {
  generatedAt: string; timezone: string; edition: string; cards: KnowledgeCard[];
  sourceErrors: Record<string, string>;
};

const fallbackDataset = dataset as CardDataset;
const remoteDatasetUrl = process.env.CARD_DATA_URL ?? 'https://raw.githubusercontent.com/Jerome-Jiayu-Lin/Quant-newsletter/main/web/data/cards.json';
const DAILY_EDITION_SIZE = 15;
const translatedTextFields = ['titleEn', 'descriptionEn', 'summaryEn', 'whyItMattersEn', 'limitationsEn'] as const;

function hasCompleteTranslation(value: unknown): value is KnowledgeCard {
  if (!value || typeof value !== 'object') return false;
  const card = value as Partial<KnowledgeCard>;
  const hasChinese = (text: unknown) => typeof text === 'string' && /[\u3400-\u9fff]/u.test(text);
  const englishText = [card.titleEn, card.descriptionEn, card.summaryEn, card.whyItMattersEn, card.limitationsEn, ...(card.keyPointsEn ?? [])].join(' ');
  return translatedTextFields.every((field) => typeof card[field] === 'string' && card[field].trim().length > 0)
    && Array.isArray(card.keyPointsEn)
    && card.keyPointsEn.length > 0
    && card.keyPointsEn.every((point) => typeof point === 'string' && point.trim().length > 0)
    && card.aiGenerated === true
    && card.summaryProvider !== 'source'
    && hasChinese(card.title)
    && hasChinese(card.description)
    && hasChinese(card.summary)
    && Array.isArray(card.keyPoints)
    && card.keyPoints.length > 0
    && card.keyPoints.every(hasChinese)
    && /[A-Za-z]/.test(englishText);
}

function isCompleteEdition(value: unknown): value is CardDataset {
  if (!value || typeof value !== 'object') return false;
  return Array.isArray((value as CardDataset).cards)
    && (value as CardDataset).cards.length >= DAILY_EDITION_SIZE
    && (value as CardDataset).cards.every(hasCompleteTranslation);
}

export async function getDataset(): Promise<CardDataset> {
  try {
    const response = await fetch(remoteDatasetUrl, {
      cache: 'no-store',
      signal: AbortSignal.timeout(4000),
    });
    if (response.ok) {
      const remoteDataset = await response.json();
      if (isCompleteEdition(remoteDataset)) return remoteDataset;
    }
  } catch {
    // Local builds and first deploys use the bundled edition until main has data.
  }
  if (!isCompleteEdition(fallbackDataset)) {
    throw new Error('The bundled Edition is not genuinely bilingual. Publish a validated AI-translated Edition.');
  }
  return fallbackDataset;
}

export function isBilingualCard(value: unknown): value is KnowledgeCard { return hasCompleteTranslation(value); }

export async function getCard(slug: string): Promise<KnowledgeCard | undefined> {
  const current = await getDataset();
  return current.cards.find((card) => card.slug === slug);
}
export function formatSingaporeTime(value: string, locale: 'zh' | 'en' = 'zh'): string {
  return new Intl.DateTimeFormat(locale === 'en' ? 'en-SG' : 'zh-CN', {
    timeZone: 'Asia/Singapore', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value));
}
