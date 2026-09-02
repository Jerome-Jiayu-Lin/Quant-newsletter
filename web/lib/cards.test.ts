import assert from 'node:assert/strict';
import test from 'node:test';
import dataset from '../data/cards.json' with { type: 'json' };
import { EditionNotFoundError, EditionUnavailableError, getDataset, getHistoricalDataset, isBilingualCard } from './cards.ts';
import { localePath, localizeCard } from './locale.ts';

test('an incomplete remote Edition cannot replace the complete bundled Edition', async () => {
  const originalFetch = globalThis.fetch;
  const incompleteEdition = { ...dataset, cards: dataset.cards.slice(0, 5) };
  globalThis.fetch = async () => new Response(JSON.stringify(incompleteEdition), { status: 200 });

  try {
    const selected = await getDataset();
    assert.equal(selected.cards.length, 15);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('a remote Edition with missing translations cannot replace the bilingual bundled Edition', async () => {
  const originalFetch = globalThis.fetch;
  const cards = dataset.cards.map((card, index) => (index === 0 ? { ...card, titleEn: '' } : card));
  globalThis.fetch = async () => new Response(JSON.stringify({ ...dataset, cards }), { status: 200 });

  try {
    const selected = await getDataset();
    assert.equal(selected.cards[0].titleEn, dataset.cards[0].titleEn);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('the English view selects translated card fields and preserves the detail path', () => {
  const card = dataset.cards[0];
  const localized = localizeCard(card, 'en');
  assert.equal(localized.title, card.titleEn);
  assert.equal(localized.summary, card.summaryEn);
  assert.ok(localized.tags.length > 0);
  assert.equal(localePath('en', `/cards/${card.slug}`), `/en/cards/${card.slug}`);
  assert.equal(localePath('zh', `/cards/${card.slug}`), `/cards/${card.slug}`);
});

test('non-empty source-only fields do not count as a bilingual translation', () => {
  const card = dataset.cards[0];
  assert.equal(isBilingualCard({
    ...card,
    title: card.titleEn,
    description: card.descriptionEn,
    summary: card.summaryEn,
    keyPoints: card.keyPointsEn,
    whyItMatters: card.whyItMattersEn,
    limitations: card.limitationsEn,
  }), false);
});

test('Chinese relevance text cannot disguise untranslated title summary and key points', () => {
  const card = dataset.cards[0];
  assert.equal(isBilingualCard({
    ...card,
    title: card.titleEn,
    description: card.descriptionEn,
    summary: card.summaryEn,
    keyPoints: card.keyPointsEn,
    whyItMatters: '可用于评估新的研究假设。',
    limitations: '尚未独立核验全文。',
  }), false);
});

test('a historical Edition is discovered through the index before its object is loaded', async () => {
  const originalFetch = globalThis.fetch;
  const edition = '2026-09-01';
  const objectKey = `editions/v1/2026/09/${edition}/quant-brief-edition.json`;
  const urls: string[] = [];
  globalThis.fetch = async (input) => {
    const url = String(input); urls.push(url);
    if (url.endsWith('/editions/v1/index.json')) return Response.json({
      schemaVersion: 1, generatedAt: 'now', latestEdition: edition,
      editions: [{ edition, objectKey, exportHash: 'a'.repeat(64), publishedAt: 'now', cardCount: 15 }],
    });
    return Response.json({ ...dataset, edition });
  };
  try {
    const selected = await getHistoricalDataset(edition);
    assert.equal(selected.cards.length, 15);
    assert.match(urls[0], /editions\/v1\/index\.json$/);
    assert.match(urls[1], new RegExp(`${edition}/quant-brief-edition\\.json$`));
  } finally { globalThis.fetch = originalFetch; }
});

test('a date absent from the public index is explicitly not found', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ schemaVersion: 1, generatedAt: 'now', latestEdition: null, editions: [] });
  try {
    await assert.rejects(getHistoricalDataset('2026-08-01'), EditionNotFoundError);
  } finally { globalThis.fetch = originalFetch; }
});

test('a broken index or missing advertised object is temporarily unavailable', async () => {
  const originalFetch = globalThis.fetch;
  let request = 0;
  globalThis.fetch = async () => {
    request += 1;
    if (request === 1) return Response.json({
      schemaVersion: 1, generatedAt: 'now', latestEdition: '2026-09-01',
      editions: [{ edition: '2026-09-01', objectKey: 'editions/v1/missing.json', exportHash: 'a'.repeat(64), publishedAt: 'now', cardCount: 15 }],
    });
    return new Response(null, { status: 404 });
  };
  try {
    await assert.rejects(getHistoricalDataset('2026-09-01'), EditionUnavailableError);
  } finally { globalThis.fetch = originalFetch; }
});
