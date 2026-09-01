import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { formatSingaporeTime, getCard } from '../../../lib/cards';

type PageProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const card = await getCard((await params).slug);
  if (!card) return {};
  return {
    title: `${card.title} · Quant Brief`, description: card.description,
    openGraph: { title: card.title, description: card.description, images: [] },
    twitter: { card: 'summary', title: card.title, description: card.description, images: [] },
  };
}

export default async function CardPage({ params }: PageProps) {
  const card = await getCard((await params).slug);
  if (!card) notFound();
  return (
    <main className="detail-shell">
      <header className="detail-topbar">
        <div className="detail-topbar-inner">
          <Link className="brand" href="/">
            <span className="brand-mark" aria-hidden="true"><span>Q</span></span>
            <span className="brand-copy"><strong>QUANT BRIEF</strong><span>RESEARCH INTELLIGENCE</span></span>
          </Link>
          <Link className="back-link" href="/">← BACK TO INDEX</Link>
        </div>
      </header>

      <article className="detail-article">
        <div className="detail-meta">
          <span className="detail-domain"><i /> {card.domain}</span>
          <span>{card.sourceName}</span>
          <span aria-hidden="true">/</span>
          <time>{formatSingaporeTime(card.publishedAt)} SGT</time>
          <span aria-hidden="true">/</span>
          <span>SIGNAL {card.id.slice(0, 6).toUpperCase()}</span>
        </div>

        <h1>{card.title}</h1>
        {card.originalTitle !== card.title ? <p className="original-title">ORIGINAL / {card.originalTitle}</p> : null}
        <p className="detail-lede">{card.description}</p>

        <div className="detail-layout">
          <div className="detail-main">
            <section className="detail-panel">
              <p className="panel-label"><span>01</span> ABSTRACT / 摘要</p>
              <p className="whitespace-pre-line">{card.summary}</p>
            </section>
            <section className="detail-panel">
              <p className="panel-label"><span>02</span> KEY FINDINGS / 关键点</p>
              <ol className="key-list">{card.keyPoints.map((point) => <li key={point}>{point}</li>)}</ol>
            </section>
          </div>
          <aside className="detail-aside">
            <section className="detail-panel dark">
              <p className="panel-label"><span>03</span> RELEVANCE</p>
              <p>{card.whyItMatters}</p>
            </section>
            <section className="detail-panel soft">
              <p className="panel-label"><span>04</span> EVIDENCE BOUNDARY</p>
              <p>{card.limitations}</p>
            </section>
          </aside>
        </div>

        <div className="source-cta">
          <div>
            <strong>回到一手来源</strong>
            <p>{card.aiGenerated ? 'AI GENERATED SUMMARY' : 'EDITORIAL SUMMARY'} / DISCOVERED BY {card.discoveredBy.join(' · ').toUpperCase()}</p>
          </div>
          <a href={card.originalUrl} rel="noreferrer" target="_blank">阅读原文 <span>↗</span></a>
        </div>
      </article>
    </main>
  );
}
