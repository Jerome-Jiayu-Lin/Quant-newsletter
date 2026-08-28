'use client';

import { useMemo, useState } from 'react';
import type { KnowledgeCard } from '../../lib/cards';
import { formatSingaporeTime } from '../../lib/cards';

const toneByDomain: Record<string, string> = {
  '量化研究': 'signal-amber', 'AI × 量化': 'signal-blue', '开源工程': 'signal-green', 'AI 工具': 'signal-orange',
};

export default function CardFeed({ cards }: { cards: KnowledgeCard[] }) {
  const domains = ['全部', ...Array.from(new Set(cards.map((card) => card.domain)))];
  const [activeDomain, setActiveDomain] = useState('全部');
  const visibleCards = useMemo(
    () => cards.filter((card) => activeDomain === '全部' || card.domain === activeDomain),
    [activeDomain, cards],
  );

  return (
    <>
      <nav aria-label="领域筛选" className="hide-scrollbar flex gap-2 overflow-x-auto py-6">
        {domains.map((domain) => (
          <button
            aria-pressed={activeDomain === domain}
            className={`shrink-0 rounded-full px-4 py-2 text-sm transition ${activeDomain === domain ? 'bg-[#173f35] text-white' : 'border border-[#173f35]/15 bg-white/35 text-[#43534c] hover:bg-white/70'}`}
            key={domain} onClick={() => setActiveDomain(domain)} type="button"
          >{domain}</button>
        ))}
      </nav>

      <div aria-live="polite" className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleCards.map((card, index) => (
          <article className="group flex min-h-[340px] flex-col rounded-[26px] border border-[#173f35]/12 bg-[#fffdf7] p-6 shadow-[0_14px_40px_rgba(29,55,45,0.06)] transition hover:-translate-y-1 hover:shadow-[0_20px_50px_rgba(29,55,45,0.11)]" key={card.id}>
            <div className="mb-7 flex items-center justify-between gap-3 text-xs">
              <span className={`signal ${toneByDomain[card.domain] ?? 'signal-neutral'}`}>{card.domain}</span>
              <span className="text-[#7b867f]">{String(index + 1).padStart(2, '0')}</span>
            </div>
            <h2 className="line-clamp-3 font-serif text-[1.65rem] leading-[1.18] tracking-[-0.02em]">{card.title}</h2>
            <p className="mt-4 line-clamp-4 text-sm leading-7 text-[#5e6d66]">{card.description}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {card.tags.slice(0, 3).map((tag) => <span className="rounded-full bg-[#173f35]/6 px-2.5 py-1 text-xs text-[#56645e]" key={tag}>{tag}</span>)}
            </div>
            <div className="mt-auto flex items-end justify-between gap-3 border-t border-[#173f35]/10 pt-5 text-xs text-[#7b867f]">
              <span>{card.sourceName}<br />{formatSingaporeTime(card.publishedAt)}</span>
              <a className="text-sm font-semibold text-[#173f35] group-hover:text-[#b34f2c]" href={`/cards/${card.slug}`}>阅读摘要 →</a>
            </div>
          </article>
        ))}
      </div>
      {visibleCards.length === 0 ? <p className="rounded-3xl border border-dashed border-[#173f35]/20 p-10 text-center text-[#5e6d66]">这个领域今天还没有通过筛选的信号。</p> : null}
    </>
  );
}
