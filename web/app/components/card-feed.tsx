'use client';

import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import type { KnowledgeCard } from '../../lib/cards';
import { formatSingaporeTime } from '../../lib/format';
import type { Locale } from '../../lib/locale';
import { localePath, localizeCard, messages } from '../../lib/locale';

const toneByDomain: Record<string, string> = {
  '量化研究': 'tone-lime', 'AI × 量化': 'tone-blue', '开源工程': 'tone-violet', 'AI 工具': 'tone-coral',
};

const sectionOrder = ['repository', 'paper', 'article', 'video'] as const;
const sectionLabels: Record<(typeof sectionOrder)[number], { zh: string; en: string }> = {
  repository: { zh: 'GitHub', en: 'GitHub' }, paper: { zh: '论文', en: 'Papers' }, article: { zh: '文章', en: 'Articles' }, video: { zh: '视频', en: 'Videos' },
};
const sectionCodes: Record<(typeof sectionOrder)[number], string> = {
  repository: 'REP', paper: 'PPR', article: 'ART', video: 'VID',
};

function contentTypeOf(card: KnowledgeCard): (typeof sectionOrder)[number] {
  if (card.contentType && sectionOrder.includes(card.contentType)) return card.contentType;
  if (card.sourceGroup === '论文') return 'paper';
  if (card.sourceGroup === '开源项目' || card.sourceGroup === 'AI 工具') return 'repository';
  if (card.sourceGroup === '视频') return 'video';
  return 'article';
}

function normalizeSearchText(value: string) {
  return value.normalize('NFKC').toLocaleLowerCase('zh-CN').trim();
}

export default function CardFeed({ cards, edition, locale }: { cards: KnowledgeCard[]; edition?: string; locale: Locale }) {
  const t = messages[locale];
  const [activeSection, setActiveSection] = useState('all');
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchableCards = useMemo(
    () => cards.map((card) => {
      const localized = localizeCard(card, locale);
      const secondary = localizeCard(card, locale === 'zh' ? 'en' : 'zh');
      return { card, fields: [localized.title, ...localized.tags, secondary.title, ...secondary.tags].map(normalizeSearchText) };
    }), [cards, locale],
  );
  const searchTerms = useMemo(
    () => normalizeSearchText(deferredQuery).split(/\s+/).filter(Boolean),
    [deferredQuery],
  );
  const visibleCards = useMemo(() => searchableCards
    .filter(({ card, fields }) => (
      (activeSection === 'all' || contentTypeOf(card) === activeSection)
      && searchTerms.every((term) => fields.some((field) => field.includes(term)))
    ))
    .map(({ card }) => card), [activeSection, searchTerms, searchableCards]);
  const visibleGroups = useMemo(() => sectionOrder
    .map((section) => ({ section, cards: visibleCards.filter((card) => contentTypeOf(card) === section) }))
    .filter(({ cards: sectionCards }) => sectionCards.length > 0), [visibleCards]);

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
      <div className="filter-console">
        <label className="search-control" htmlFor="card-search">
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="6.75" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <path d="m16 16 4 4" fill="none" stroke="currentColor" strokeLinecap="square" strokeWidth="1.5" />
          </svg>
          <input
            autoComplete="off"
            id="card-search"
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t.searchPlaceholder}
            ref={searchInputRef}
            type="search"
            value={query}
          />
          {query ? (
            <button aria-label={t.clearSearch} onClick={() => setQuery('')} type="button">CLEAR</button>
          ) : <kbd>CTRL K</kbd>}
        </label>

        <nav aria-label={t.filtersAria} className="filter-tabs">
          {['all', ...sectionOrder].map((section) => (
            <button
              aria-pressed={activeSection === section}
              className={activeSection === section ? 'active' : ''}
              key={section}
              onClick={() => setActiveSection(section)}
              type="button"
            >
              <span>{section === 'all' ? 'ALL' : sectionCodes[section]}</span>
              {section === 'all' ? t.all : sectionLabels[section][locale]}
            </button>
          ))}
        </nav>

        <p aria-live="polite" className="result-count">
          <i /> {searchTerms.length ? `MATCHED ${String(visibleCards.length).padStart(2, '0')}` : `INDEXED ${String(cards.length).padStart(2, '0')}`}
        </p>
      </div>

      <div aria-live="polite" className="signal-groups">
        {visibleGroups.map(({ section, cards: sectionCards }, groupIndex) => (
          <section className="signal-group" key={section}>
            <div className="group-heading">
              <div><span>0{groupIndex + 1} / {sectionCodes[section]}</span><h3>{sectionLabels[section][locale]}</h3></div>
              <p>SELECTED SIGNALS <strong>{String(sectionCards.length).padStart(2, '0')}</strong></p>
            </div>
            <div className="card-grid">
              {sectionCards.map((card, index) => {
                const localized = localizeCard(card, locale);
                return (
                <article className={`signal-card ${toneByDomain[card.domain] ?? 'tone-neutral'}`} key={card.id} lang={messages[locale].htmlLang}>
                  <span className="card-trace" aria-hidden="true" />
                  <div className="card-meta">
                    <span className="domain-label"><i /> {localized.domain}</span>
                    <span className="card-index">{sectionCodes[section]}-{String(index + 1).padStart(2, '0')}</span>
                  </div>
                  <h4>{localized.title}</h4>
                  <p className="card-description">{localized.description}</p>
                  <div className="tag-list">
                    {localized.tags.slice(0, 3).map((tag) => <span key={tag}>#{tag}</span>)}
                  </div>
                  <div className="card-footer">
                    <div><span>{card.sourceName}</span><time>{formatSingaporeTime(card.publishedAt, locale)} SGT</time></div>
                    <a href={localePath(locale, edition ? `/editions/${edition}/cards/${card.slug}` : `/cards/${card.slug}`)} aria-label={`${t.readSummary}: ${localized.title}`}><span>{t.openSignal}</span><b aria-hidden="true">↗</b></a>
                  </div>
                </article>);
              })}
            </div>
          </section>
        ))}
      </div>

      {visibleCards.length === 0 ? (
        <div className="empty-state">
          <span>NO SIGNAL</span>
          <h3>{t.noSignal}</h3>
          <p>{query ? t.shorterQuery : t.emptySection}</p>
          {query ? <button onClick={() => setQuery('')} type="button">{t.clearSearch}</button> : null}
        </div>
      ) : null}
    </>
  );
}
