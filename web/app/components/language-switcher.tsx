import type { Locale } from '../../lib/locale';
import { messages } from '../../lib/locale';

export default function LanguageSwitcher({ locale, path = '/' }: { locale: Locale; path?: string }) {
  const englishPath = `/en${path === '/' ? '' : path}`;
  return (
    <nav aria-label={messages[locale].localeLabel} className="language-switcher">
      <a aria-current={locale === 'zh' ? 'page' : undefined} href={path} hrefLang="zh-CN" lang="zh-CN">中文</a>
      <span aria-hidden="true">/</span>
      <a aria-current={locale === 'en' ? 'page' : undefined} href={englishPath} hrefLang="en" lang="en">EN</a>
    </nav>
  );
}
