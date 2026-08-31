'use client';

import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import type { KnowledgeCard } from '../../lib/cards';
import { formatSingaporeTime } from '../../lib/cards';

const toneByDomain: Record<string, string> = {
  '量化研究': 'signal-amber', 'AI × 量化': 'signal-blue', '开源工程': 'signal-green', 'AI 工具': 'signal-orange',
};

function normalizeSearchText(value: string) {
  return value.normalize('NFKC').toLocaleLowerCase('zh-CN').trim();
}

export default function CardFeed({ cards }: { cards: KnowledgeCard[] }) {
  const domains = ['全部', ...Array.from(new Set(cards.map((card) => card.domain)))];
  const [activeDomain, setActiveDomain] = useState('全部');
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchableCards = useMemo(
    () => cards.map((card) => ({
      card,
      fields: [card.title, ...card.tags].map(normalizeSearchText),
    })),
    [cards],
  );
  const searchTerms = useMemo(
    () => normalizeSearchText(deferredQuery).split(/\s+/).filter(Boolean),
    [deferredQuery],
  );
  const visibleCards = useMemo(() => searchableCards
    .filter(({ card, fields }) => (
      (activeDomain === '全部' || card.domain === activeDomain)
      && searchTerms.every((term) => fields.some((field) => field.includes(term)))
    ))
    .map(({ card }) => card), [activeDomain, searchTerms, searchableCards]);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLocaleLowerCase() === 'k') {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
      if (event.key === 'Escape' && document.activeElement === searchInputRef.current) {
        setQuery('');
        searchInputRef.current?.blur();
      }
    };
    window.addEventListener('keydown', handleShortcut);
    return () => window.removeEventListener('keydown', handleShortcut);
  }, []);

  return (
    <>
      <div className="py-6">
        <div className="flex flex-col gap-3 rounded-[22px] border border-[#173f35]/12 bg-[#fffdf7]/80 p-3 shadow-[0_10px_32px_rgba(29,55,45,0.045)] sm:flex-row sm:items-center">
          <label className="group flex min-w-0 flex-1 items-center gap-3 rounded-2xl bg-white px-4 py-3 ring-1 ring-[#173f35]/10 transition focus-within:ring-2 focus-within:ring-[#b34f2c]/55" htmlFor="card-search">
            <svg aria-hidden="true" className="h-5 w-5 shrink-0 text-[#6d7973]" fill="none" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.8" />
              <path d="m16.5 16.5 4 4" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
            </svg>
            <input
              autoComplete="off"
              className="min-w-0 flex-1 bg-transparent text-[15px] text-[#1f2a25] outline-none placeholder:text-[#8a938e]"
              id="card-search"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索标题或标签…"
              ref={searchInputRef}
              type="search"
              value={query}
            />
            {query ? (
              <button aria-label="清空搜索" className="rounded-lg px-2 py-1 text-xs text-[#6d7973] hover:bg-[#173f35]/6 hover:text-[#173f35]" onClick={() => setQuery('')} type="button">清空</button>
            ) : <kbd className="hidden rounded-md border border-[#173f35]/12 bg-[#f5f1e8] px-2 py-1 text-[11px] text-[#7b867f] sm:inline">Ctrl K</kbd>}
          </label>
          <p aria-live="polite" className="shrink-0 px-2 text-xs text-[#6d7973]">
            {searchTerms.length ? `找到 ${visibleCards.length} 条` : `共 ${cards.length} 条信号`}
          </p>
        </div>

        <nav aria-label="领域筛选" className="hide-scrollbar flex gap-2 overflow-x-auto pt-4">
          {domains.map((domain) => (
            <button
              aria-pressed={activeDomain === domain}
              className={`shrink-0 rounded-full px-4 py-2 text-sm transition ${activeDomain === domain ? 'bg-[#173f35] text-white' : 'border border-[#173f35]/15 bg-white/35 text-[#43534c] hover:bg-white/70'}`}
              key={domain} onClick={() => setActiveDomain(domain)} type="button"
            >{domain}</button>
          ))}
        </nav>
      </div>

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
      {visibleCards.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-[#173f35]/20 p-10 text-center text-[#5e6d66]">
          <p className="font-serif text-xl text-[#33443c]">没有找到匹配的信号</p>
          <p className="mt-2 text-sm">{query ? '试试更短的关键词，或切换到“全部”领域。' : '这个领域今天还没有信号。'}</p>
          {query ? <button className="mt-5 rounded-full bg-[#173f35] px-4 py-2 text-sm text-white hover:bg-[#285b4f]" onClick={() => setQuery('')} type="button">清空搜索</button> : null}
        </div>
      ) : null}
    </>
  );
}
