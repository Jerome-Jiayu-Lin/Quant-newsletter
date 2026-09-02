import CardFeed from './card-feed';
import EditionHistory from './edition-history';
import LanguageSwitcher from './language-switcher';
import DocumentLanguage from './document-language';
import type { CardDataset } from '../../lib/cards';
import { getDataset, getEditionIndex } from '../../lib/cards';
import type { Locale } from '../../lib/locale';
import { messages } from '../../lib/locale';

const contentTypes = ['repository', 'paper', 'article', 'video'] as const;

function resolveContentType(sourceGroup: string, contentType?: string) {
  if (contentType && contentTypes.includes(contentType as (typeof contentTypes)[number])) return contentType;
  if (sourceGroup === '论文') return 'paper';
  if (sourceGroup === '开源项目' || sourceGroup === 'AI 工具') return 'repository';
  if (sourceGroup === '视频') return 'video';
  return 'article';
}

export default async function HomePage({ locale, editionDate, initialDataset }: { locale: Locale; editionDate?: string; initialDataset?: CardDataset }) {
  const dataset = initialDataset ?? await getDataset();
  const editionIndex = await getEditionIndex();
  const t = messages[locale];
  const failedSources = Object.keys(dataset.sourceErrors ?? {}).length;
  const paperCount = dataset.cards.filter((card) => resolveContentType(card.sourceGroup, card.contentType) === 'paper').length;
  const engineeringCount = dataset.cards.filter((card) => resolveContentType(card.sourceGroup, card.contentType) === 'repository').length;
  const sourceCount = new Set(dataset.cards.map((card) => card.sourceName)).size;

  return (
    <main className="site-shell" lang={t.htmlLang}>
      <DocumentLanguage locale={locale} />
      <header className="topbar"><div className="topbar-inner">
        <a className="brand" href="#top" aria-label={t.homeAria}><span className="brand-mark" aria-hidden="true"><span>J</span></span><span className="brand-copy"><strong>JEROME BRIEF</strong><span>RESEARCH INTELLIGENCE</span></span></a>
        <div className="topbar-status"><span className="system-state"><i /> {t.systemOnline}</span><span className="topbar-rule" aria-hidden="true" /><span>SGT · {dataset.edition}</span><LanguageSwitcher locale={locale} /></div>
      </div></header>

      <section id="top" className="hero-section"><div className="hero-grid">
        <div className="hero-copy"><p className="tech-label"><span>01</span> {t.dailyLabel} / {dataset.edition}</p><h1>{t.heroLead}<br /><span>{t.heroAccent}</span></h1><p className="hero-description">{t.heroDescription}</p><div className="hero-actions"><a className="primary-action" href="#signals">{t.browse} <span>↓</span></a><p>{failedSources ? t.delayedSources(failedSources) : t.allSourcesReady}</p></div></div>
        <aside className="signal-console" aria-label={locale === 'zh' ? '今日信号概览' : "Today's signal overview"}><div className="console-head"><span>SIGNAL MATRIX</span><span className="console-live"><i /> LIVE</span></div><div className="console-visual" aria-hidden="true"><span className="scan-line" /><span className="vector vector-a" /><span className="vector vector-b" /><span className="vector vector-c" /><span className="node node-a" /><span className="node node-b" /><span className="node node-c" /><span className="node node-d" /><span className="matrix-code">JBR / {dataset.edition.replaceAll('.', '')}</span></div><div className="metric-grid"><div><span>{t.selected}</span><strong>{String(dataset.cards.length).padStart(2, '0')}</strong><small>SIGNALS</small></div><div><span>{t.papers}</span><strong>{String(paperCount).padStart(2, '0')}</strong><small>PAPERS</small></div><div><span>{t.repositories}</span><strong>{String(engineeringCount).padStart(2, '0')}</strong><small>REPOS</small></div><div><span>{t.sources}</span><strong>{String(sourceCount).padStart(2, '0')}</strong><small>SOURCES</small></div></div></aside>
      </div></section>

      <section className="feed-section" id="signals"><div className="section-intro"><p className="tech-label"><span>02</span> CURATED INDEX</p><div><h2>{editionDate ? t.archiveTitle : t.indexTitle}</h2><p>{t.indexDescription}</p></div></div><EditionHistory currentEdition={dataset.edition.replaceAll('.', '-')} index={editionIndex} locale={locale} /><CardFeed cards={dataset.cards} edition={editionDate} locale={locale} /></section>
      <footer className="site-footer"><div className="brand footer-brand"><span className="brand-mark mini" aria-hidden="true"><span>J</span></span><span className="brand-copy"><strong>JEROME BRIEF</strong><span>RESEARCH INTELLIGENCE</span></span></div><p>{t.footer}</p><p className="footer-process">FETCH <i /> RANK <i /> SUMMARIZE <i /> TRACE</p></footer>
    </main>
  );
}
