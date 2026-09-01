import assert from 'node:assert/strict';
import test from 'node:test';
import dataset from '../data/cards.json' with { type: 'json' };
import { getDataset } from './cards.ts';

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
