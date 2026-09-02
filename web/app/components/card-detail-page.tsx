import Link from 'next/link';
import { notFound } from 'next/navigation';
import { EditionUnavailableError, formatSingaporeTime, getCard, getHistoricalCard } from '../../lib/cards';
import type { Locale } from '../../lib/locale';
import { localePath, localizeCard, messages } from '../../lib/locale';
import LanguageSwitcher from './language-switcher';
import DocumentLanguage from './document-language';
import EditionUnavailablePage from './edition-unavailable-page';

export default async function CardDetailPage({ slug, locale, edition }: { slug: string; locale: Locale; edition?: string }) {
  let card;
  let unavailable = false;
  try {
    card = edition ? await getHistoricalCard(edition, slug) : await getCard(slug);
  } catch (error) {
    if (error instanceof EditionUnavailableError && edition) unavailable = true;
    else throw error;
  }
  if (unavailable && edition) return <EditionUnavailablePage edition={edition} locale={locale} />;
  if (!card) notFound();
  const t = messages[locale];
  const localized = localizeCard(card, locale);
  const homePath = edition ? `/editions/${edition}` : '';
  const cardPath = edition ? `/editions/${edition}/cards/${card.slug}` : `/cards/${card.slug}`;

  return (
    <main className="detail-shell" lang={t.htmlLang}>
      <DocumentLanguage locale={locale} />
      <header className="detail-topbar"><div className="detail-topbar-inner">
        <Link className="brand" href={localePath(locale, homePath)}><span className="brand-mark" aria-hidden="true"><span>J</span></span><span className="brand-copy"><strong>JEROME BRIEF</strong><span>RESEARCH INTELLIGENCE</span></span></Link>
        <div className="detail-navigation"><LanguageSwitcher locale={locale} path={cardPath} /><Link className="back-link" href={localePath(locale, homePath)}>{t.back}</Link></div>
      </div></header>
      <article className="detail-article">
        <div className="detail-meta"><span className="detail-domain"><i /> {localized.domain}</span><span>{card.sourceName}</span><span aria-hidden="true">/</span><time>{formatSingaporeTime(card.publishedAt, locale)} SGT</time><span aria-hidden="true">/</span><span>SIGNAL {card.id.slice(0, 6).toUpperCase()}</span></div>
        <h1>{localized.title}</h1>
        {card.originalTitle !== localized.title ? <p className="original-title">{t.original} / {card.originalTitle}</p> : null}
        <p className="detail-lede">{localized.description}</p>
        <div className="detail-layout"><div className="detail-main">
          <section className="detail-panel"><p className="panel-label"><span>01</span> {t.abstract}</p><p className="whitespace-pre-line">{localized.summary}</p></section>
          <section className="detail-panel"><p className="panel-label"><span>02</span> {t.keyFindings}</p><ol className="key-list">{localized.keyPoints.map((point) => <li key={point}>{point}</li>)}</ol></section>
        </div><aside className="detail-aside">
          <section className="detail-panel dark"><p className="panel-label"><span>03</span> {t.relevance}</p><p>{localized.whyItMatters}</p></section>
          <section className="detail-panel soft"><p className="panel-label"><span>04</span> {t.evidence}</p><p>{localized.limitations}</p></section>
        </aside></div>
        <div className="source-cta"><div><strong>{t.primarySource}</strong><p>{card.aiGenerated ? 'AI GENERATED SUMMARY' : 'EDITORIAL SUMMARY'} / DISCOVERED BY {card.discoveredBy.join(' · ').toUpperCase()}</p></div><a href={card.originalUrl} rel="noreferrer" target="_blank">{t.readOriginal} <span>↗</span></a></div>
      </article>
    </main>
  );
}
