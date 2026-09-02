'use client';

import { useEffect } from 'react';
import type { Locale } from '../../lib/locale';
import { messages } from '../../lib/locale';

export default function DocumentLanguage({ locale }: { locale: Locale }) {
  useEffect(() => {
    document.documentElement.lang = messages[locale].htmlLang;
  }, [locale]);
  return null;
}
