import dataset from '../data/cards.json' with { type: 'json' };
import { readBoundPublicEdition } from './public-edition-storage.ts';

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
  schemaVersion?: number; generatedAt: string; timezone: string; edition: string; cards: KnowledgeCard[];
  sourceErrors?: Record<string, string>;
};

export type EditionIndexEntry = {
  edition: string; objectKey: string; exportHash: string; publishedAt: string; cardCount: number;
};

export type EditionIndex = {
  schemaVersion: 1; generatedAt: string; latestEdition: string | null; editions: EditionIndexEntry[];
};

export class EditionNotFoundError extends Error {}
export class EditionUnavailableError extends Error {}

const fallbackDataset = dataset as CardDataset;
const remoteDatasetUrl = process.env.CARD_DATA_URL ?? 'https://raw.githubusercontent.com/Jerome-Jiayu-Lin/Quant-newsletter/main/web/data/cards.json';
const publicDataOrigin = (process.env.PUBLIC_EDITION_ORIGIN ?? 'https://data.jeromebrief.com').replace(/\/$/, '');
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

function isEditionIndex(value: unknown): value is EditionIndex {
  if (!value || typeof value !== 'object') return false;
  const index = value as Partial<EditionIndex>;
  return index.schemaVersion === 1
    && (index.latestEdition === null || typeof index.latestEdition === 'string')
    && Array.isArray(index.editions)
    && index.editions.every((entry) => (
      /^\d{4}-\d{2}-\d{2}$/.test(entry.edition)
      && typeof entry.objectKey === 'string'
      && /^editions\/v1\//.test(entry.objectKey)
      && /^[0-9a-f]{64}$/.test(entry.exportHash)
      && typeof entry.cardCount === 'number'
    ));
}

async function fetchJson(url: string): Promise<{ response: Response; value?: unknown }> {
  const response = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(4000) });
  if (!response.ok) return { response };
  return { response, value: await response.json() };
}

async function readPublicJson(key: string): Promise<{ found: boolean; value?: unknown }> {
  const bound = await readBoundPublicEdition(key);
  if (bound !== null) return { found: true, value: bound };
  const result = await fetchJson(`${publicDataOrigin}/${key}`);
  return { found: result.response.ok, value: result.value };
}

export async function getEditionIndex(): Promise<EditionIndex | null> {
  try {
    const result = await readPublicJson('editions/v1/index.json');
    return result.found && isEditionIndex(result.value) ? result.value : null;
  } catch {
    return null;
  }
}

async function fetchIndexedEdition(entry: EditionIndexEntry): Promise<CardDataset> {
  const result = await readPublicJson(entry.objectKey);
  if (!result.found || !isCompleteEdition(result.value) || result.value.edition.replaceAll('.', '-') !== entry.edition) {
    throw new EditionUnavailableError(entry.edition);
  }
  return result.value;
}

export async function getHistoricalDataset(edition: string): Promise<CardDataset> {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(edition)) throw new EditionNotFoundError(edition);
  let index: EditionIndex;
  try {
    const result = await readPublicJson('editions/v1/index.json');
    if (!result.found || !isEditionIndex(result.value)) throw new EditionUnavailableError(edition);
    index = result.value;
  } catch (error) {
    if (error instanceof EditionUnavailableError) throw error;
    throw new EditionUnavailableError(edition, { cause: error });
  }
  const entry = index.editions.find((candidate) => candidate.edition === edition);
  if (!entry) throw new EditionNotFoundError(edition);
  try {
    return await fetchIndexedEdition(entry);
  } catch (error) {
    if (error instanceof EditionUnavailableError) throw error;
    throw new EditionUnavailableError(edition, { cause: error });
  }
}

export async function getDataset(): Promise<CardDataset> {
  const index = await getEditionIndex();
  const latest = index?.latestEdition
    ? index.editions.find((entry) => entry.edition === index.latestEdition)
    : undefined;
  if (latest) {
    try {
      return await fetchIndexedEdition(latest);
    } catch {
      // Migration safety: fall through to the validated latest-JSON compatibility path.
    }
  }
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
export async function getHistoricalCard(edition: string, slug: string): Promise<KnowledgeCard | undefined> {
  const current = await getHistoricalDataset(edition);
  return current.cards.find((card) => card.slug === slug);
}
