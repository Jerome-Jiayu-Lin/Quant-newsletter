import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="route-state">
      <span>404 / EDITION NOT FOUND</span>
      <h1>这个 Edition 不存在</h1>
      <p>The requested Edition is not present in the verified public history index.</p>
      <Link href="/">返回最新 Edition / Return to latest</Link>
    </main>
  );
}
