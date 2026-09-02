export function formatSingaporeTime(value: string, locale: 'zh' | 'en' = 'zh'): string {
  return new Intl.DateTimeFormat(locale === 'en' ? 'en-SG' : 'zh-CN', {
    timeZone: 'Asia/Singapore', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value));
}
