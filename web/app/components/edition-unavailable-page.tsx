import Link from 'next/link';
import type { Locale } from '../../lib/locale';
import { localePath, messages } from '../../lib/locale';

export default function EditionUnavailablePage({ edition, locale }: { edition: string; locale: Locale }) {
  const t = messages[locale];
  return (
    <main className="route-state" lang={t.htmlLang}>
      <span>503 / EDITION UNAVAILABLE</span>
      <h1>{t.editionUnavailable}</h1>
      <p>{t.editionUnavailableDescription(edition)}</p>
      <Link href={localePath(locale)}>{t.returnLatest}</Link>
    </main>
  );
}
