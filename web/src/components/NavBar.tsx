"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Sell decision" },
  { href: "/coverage", label: "Data Coverage" },
  { href: "/forecast", label: "Forecast" },
  { href: "/recommend", label: "Recommendation" },
];

export default function NavBar() {
  const path = usePathname();
  return (
    <>
      <a
        href="#main-content"
        className="sr-only fixed left-2 top-2 z-50 rounded bg-white px-3 py-2 text-sm font-semibold text-gray-900 focus:not-sr-only"
      >
        Skip to main content
      </a>
      <nav
        aria-label="Primary navigation"
        className="flex flex-col gap-2 bg-gray-900 px-4 py-3 text-white sm:flex-row sm:items-center sm:gap-6"
      >
        <Link href="/" className="shrink-0 text-sm font-semibold tracking-tight focus-visible:outline-white">
          MandiPulse India
        </Link>
      <div className="flex max-w-full gap-1 overflow-x-auto sm:gap-2">
        {LINKS.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            aria-current={l.href === "/" ? (path === "/" ? "page" : undefined) : path?.startsWith(l.href) ? "page" : undefined}
            className={`whitespace-nowrap rounded px-2 py-1 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white sm:px-3 ${
              l.href === "/" ? path === "/" : path?.startsWith(l.href)
                ? "bg-gray-700 text-white"
                : "text-gray-300 hover:text-white"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
      </nav>
    </>
  );
}
