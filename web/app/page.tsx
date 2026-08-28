import CardFeed from './components/card-feed';
import { getDataset } from '../lib/cards';

export default async function Home() {
  const dataset = await getDataset();
  const failedSources = Object.keys(dataset.sourceErrors).length;
  return (
    <main className="min-h-screen bg-[#f5f1e8] text-[#1f2a25]">
      <header className="border-b border-[#1f2a25]/10 bg-[#f5f1e8]/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 sm:px-8">
          <a className="flex items-center gap-3" href="#top" aria-label="Quant Brief 首页">
            <span className="grid h-10 w-10 place-items-center rounded-full bg-[#173f35] font-serif text-lg text-[#f7d873]">Q</span>
            <span><strong className="block font-serif text-lg leading-none">Quant Brief</strong><span className="text-xs text-[#5e6d66]">研究者的每日信号</span></span>
          </a>
          <div className="flex items-center gap-3 text-sm text-[#5e6d66]">
            <span className="hidden sm:inline">新加坡 · {dataset.edition}</span>
            <span className="rounded-full border border-[#173f35]/15 bg-white/50 px-3 py-1.5">今日 {dataset.cards.length} 条</span>
          </div>
        </div>
      </header>

      <section id="top" className="mx-auto max-w-6xl px-5 pb-12 pt-12 sm:px-8 sm:pt-16">
        <div className="grid gap-8 border-b border-[#1f2a25]/15 pb-10 lg:grid-cols-[1fr_300px] lg:items-end">
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.22em] text-[#b34f2c]">Daily intelligence · {dataset.edition}</p>
            <h1 className="max-w-3xl font-serif text-4xl leading-[1.08] tracking-[-0.03em] sm:text-6xl">从噪音里，留下今天真正值得研究的信号。</h1>
          </div>
          <div>
            <p className="text-sm leading-7 text-[#5e6d66]">聚合量化论文、开源项目与 AI 工程进展。每张卡片先告诉你为什么值得看，再带你进入结构化摘要与原文。</p>
            <p className="mt-3 text-xs text-[#7b867f]">{failedSources ? `${failedSources} 个来源本轮暂不可用，其余来源已正常更新。` : '本轮已完成全部来源检查。'}</p>
          </div>
        </div>
        <CardFeed cards={dataset.cards} />
        <footer className="mt-10 flex flex-col justify-between gap-4 border-t border-[#1f2a25]/15 pt-6 text-xs leading-5 text-[#6d7973] sm:flex-row">
          <p>摘要用于研究导航，不构成投资建议。所有结论请回到原文核验。</p><p>自动采集 · 去重排序 · 原文可追溯</p>
        </footer>
      </section>
    </main>
  );
}
