import type { KnowledgeCard } from './cards';

export type Locale = 'zh' | 'en';

export const messages = {
  zh: {
    htmlLang: 'zh-CN', homeAria: 'Jerome Brief 首页', systemOnline: 'SYSTEM ONLINE',
    dailyLabel: 'DAILY RESEARCH SIGNALS', heroLead: '把市场噪声', heroAccent: '压缩成可研究的信号。',
    heroDescription: '聚合量化论文、开源项目与 AI 工程进展。每条信号经过筛选、排序与结构化，帮助研究者更快抵达真正重要的信息。',
    browse: '浏览今日信号', allSourcesReady: '全部数据源检查完成，管线运行正常', delayedSources: (count: number) => `${count} 个数据源延迟，其余管线运行正常`,
    selected: '今日入选', papers: '研究论文', repositories: '工程项目', sources: '独立来源',
    indexTitle: '今日信号库', indexDescription: '按内容类型浏览，或直接搜索标题与标签。',
    searchPlaceholder: '搜索标题或标签', clearSearch: '清空搜索', filtersAria: '内容板块筛选', all: '全部',
    openSignal: '打开信号', readSummary: '阅读摘要', noSignal: '没有找到匹配的信号',
    shorterQuery: '试试更短的关键词，或切换到全部板块。', emptySection: '这个板块今天还没有信号。',
    footer: '摘要用于研究导航，不构成投资建议。所有结论请回到原文核验。', back: '← 返回信号库',
    original: '原始标题', abstract: '摘要', keyFindings: '关键点', relevance: '研究价值', evidence: '证据边界',
    primarySource: '回到一手来源', readOriginal: '阅读原文', localeLabel: '语言选择',
    archive: '历史 EDITIONS', historyAria: '历史 Edition 导航', archiveTitle: '历史信号库',
    editionUnavailable: '这个 Edition 暂时不可用', editionUnavailableDescription: (edition: string) => `${edition} 已列入历史索引，但远端内容暂时无法完成验证。`, returnLatest: '返回最新 Edition',
  },
  en: {
    htmlLang: 'en', homeAria: 'Jerome Brief home', systemOnline: 'SYSTEM ONLINE',
    dailyLabel: 'DAILY RESEARCH SIGNALS', heroLead: 'Compress market noise', heroAccent: 'into research-ready signals.',
    heroDescription: 'A curated stream of quantitative research, open-source projects, and AI engineering advances—screened, ranked, and structured for faster research decisions.',
    browse: "Browse today's signals", allSourcesReady: 'All sources checked. Pipeline operating normally.', delayedSources: (count: number) => `${count} sources delayed. Remaining pipeline operating normally.`,
    selected: 'Selected today', papers: 'Research papers', repositories: 'Engineering projects', sources: 'Independent sources',
    indexTitle: "Today's signal index", indexDescription: 'Browse by content type or search titles and tags.',
    searchPlaceholder: 'Search titles or tags', clearSearch: 'Clear search', filtersAria: 'Filter content sections', all: 'All',
    openSignal: 'Open signal', readSummary: 'Read summary', noSignal: 'No matching signals',
    shorterQuery: 'Try a shorter query or switch to all sections.', emptySection: 'No signals in this section today.',
    footer: 'Summaries are for research navigation, not investment advice. Verify every conclusion against the primary source.', back: '← BACK TO INDEX',
    original: 'ORIGINAL', abstract: 'ABSTRACT', keyFindings: 'KEY FINDINGS', relevance: 'RELEVANCE', evidence: 'EVIDENCE BOUNDARY',
    primarySource: 'Return to the primary source', readOriginal: 'Read original', localeLabel: 'Language selection',
    archive: 'EDITION HISTORY', historyAria: 'Historical Edition navigation', archiveTitle: 'Historical signal index',
    editionUnavailable: 'This Edition is temporarily unavailable', editionUnavailableDescription: (edition: string) => `${edition} is listed in the history index, but its remote content cannot currently be verified.`, returnLatest: 'Return to latest Edition',
  },
} as const;

const domainLabels: Record<string, { zh: string; en: string }> = {
  '量化研究': { zh: '量化研究', en: 'Quantitative Research' },
  'AI × 量化': { zh: 'AI × 量化', en: 'AI × Quant' },
  '开源工程': { zh: '开源工程', en: 'Open-source Engineering' },
  'AI 工具': { zh: 'AI 工具', en: 'AI Tools' },
};

export function localePath(locale: Locale, path = ''): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return locale === 'en' ? `/en${normalized === '/' ? '' : normalized}` : normalized;
}

export function localizeCard(card: KnowledgeCard, locale: Locale) {
  const featureTags = card.features?.map((feature) => feature.label[locale]).filter(Boolean) ?? [];
  return {
    title: locale === 'en' ? card.titleEn : card.title,
    description: locale === 'en' ? card.descriptionEn : card.description,
    summary: locale === 'en' ? card.summaryEn : card.summary,
    keyPoints: locale === 'en' ? card.keyPointsEn : card.keyPoints,
    whyItMatters: locale === 'en' ? card.whyItMattersEn : card.whyItMatters,
    limitations: locale === 'en' ? card.limitationsEn : card.limitations,
    tags: locale === 'en' ? (card.tagsEn?.length ? card.tagsEn : featureTags) : card.tags,
    domain: domainLabels[card.domain]?.[locale] ?? card.domain,
  };
}
