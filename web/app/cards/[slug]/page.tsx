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
    <main className="min-h-screen bg-[#f5f1e8] text-[#1f2a25]">
      <header className="border-b border-[#1f2a25]/10 px-5 py-5 sm:px-8">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4">
          <Link className="flex items-center gap-3" href="/"><span className="grid h-9 w-9 place-items-center rounded-full bg-[#173f35] font-serif text-[#f7d873]">Q</span><strong className="font-serif">Quant Brief</strong></Link>
          <Link className="text-sm text-[#5e6d66] hover:text-[#b34f2c]" href="/">← 返回今日简报</Link>
        </div>
      </header>
      <article className="mx-auto max-w-4xl px-5 py-10 sm:px-8 sm:py-16">
        <div className="mb-7 flex flex-wrap items-center gap-3 text-xs text-[#6d7973]">
          <span className="signal signal-amber">{card.domain}</span><span>{card.sourceName}</span><span aria-hidden="true">·</span><time>{formatSingaporeTime(card.publishedAt)}</time>
        </div>
        <h1 className="font-serif text-4xl leading-[1.08] tracking-[-0.03em] sm:text-6xl">{card.title}</h1>
        {card.originalTitle !== card.title ? <p className="mt-4 text-sm italic leading-6 text-[#7b867f]">原标题：{card.originalTitle}</p> : null}
        <p className="mt-7 border-l-2 border-[#d89a45] pl-5 text-lg leading-8 text-[#4d5d55]">{card.description}</p>
        <div className="mt-10 grid gap-5 lg:grid-cols-[1fr_250px]">
          <div className="space-y-5">
            <section className="summary-panel"><p className="eyebrow">摘要</p><p className="mt-3 whitespace-pre-line leading-8 text-[#43534c]">{card.summary}</p></section>
            <section className="summary-panel"><p className="eyebrow">关键点</p><ul className="mt-4 space-y-3 text-sm leading-7 text-[#43534c]">{card.keyPoints.map((point) => <li className="flex gap-3" key={point}><span className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-[#b34f2c]" />{point}</li>)}</ul></section>
          </div>
          <aside className="space-y-4">
            <section className="rounded-3xl bg-[#173f35] p-5 text-white"><p className="eyebrow text-[#f7d873]">为什么值得看</p><p className="mt-3 text-sm leading-7 text-white/78">{card.whyItMatters}</p></section>
            <section className="rounded-3xl border border-[#173f35]/12 bg-white/50 p-5"><p className="eyebrow">证据边界</p><p className="mt-3 text-sm leading-7 text-[#5e6d66]">{card.limitations}</p></section>
          </aside>
        </div>
        <div className="mt-8 rounded-3xl border border-[#173f35]/12 bg-[#fffdf7] p-6 sm:flex sm:items-center sm:justify-between sm:gap-5">
          <div><p className="text-sm font-semibold">回到一手来源</p><p className="mt-1 text-xs text-[#7b867f]">{card.aiGenerated ? 'AI 生成摘要' : '来源摘要整理'} · 经 {card.discoveredBy.join('、')} 发现</p></div>
          <a className="mt-4 inline-flex rounded-full bg-[#b34f2c] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#913b20] sm:mt-0" href={card.originalUrl} rel="noreferrer" target="_blank">阅读原文 ↗</a>
        </div>
      </article>
    </main>
  );
}
