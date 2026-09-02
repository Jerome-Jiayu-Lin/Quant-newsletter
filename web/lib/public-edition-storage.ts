type PublicEditionObject = {
  json<T = unknown>(): Promise<T>;
};

type PublicEditionBucket = {
  get(key: string): Promise<PublicEditionObject | null>;
};

export async function readPublicEditionObject(
  bucket: PublicEditionBucket,
  key: string,
): Promise<unknown | null> {
  const object = await bucket.get(key);
  return object ? object.json() : null;
}

export async function readBoundPublicEdition(key: string): Promise<unknown | null> {
  try {
    const { env } = await import('cloudflare:workers');
    const bucket = (env as unknown as { PUBLIC_EDITIONS?: PublicEditionBucket }).PUBLIC_EDITIONS;
    return bucket ? readPublicEditionObject(bucket, key) : null;
  } catch {
    // Node-based tests and non-Workers builds continue through the HTTP migration path.
    return null;
  }
}
