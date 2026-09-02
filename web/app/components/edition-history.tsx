import Link from 'next/link';
import type { EditionIndex } from '../../lib/cards';
import type { Locale } from '../../lib/locale';
import { localePath, messages } from '../../lib/locale';

export default function EditionHistory({ index, currentEdition, locale }: { index: EditionIndex | null; currentEdition: string; locale: Locale }) {
  if (!index?.editions.length) return null;
  const t = messages[locale];
  return (
    <nav aria-label={t.historyAria} className="edition-history">
      <span>{t.archive}</span>
      <div>
        {index.editions.slice(0, 8).map((entry) => (
          <Link
            aria-current={entry.edition === currentEdition ? 'page' : undefined}
            href={localePath(locale, `/editions/${entry.edition}`)}
            key={entry.edition}
          >
            {entry.edition}
          </Link>
        ))}
      </div>
    </nav>
  );
}
