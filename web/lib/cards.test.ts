import assert from 'node:assert/strict';
import test from 'node:test';
import dataset from '../data/cards.json' with { type: 'json' };
import { getDataset, isBilingualCard } from './cards.ts';
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
