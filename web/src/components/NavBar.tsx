"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/coverage", label: "Data Coverage" },
  { href: "/forecast", label: "Forecast" },
  { href: "/recommend", label: "Recommendation" },
];

export default function NavBar() {
  const path = usePathname();
  return (
    <nav className="bg-gray-900 text-white px-4 py-3 flex items-center gap-6">
      <span className="font-semibold tracking-tight text-sm">MandiPulse India</span>
      <div className="flex gap-4">
        {LINKS.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`text-sm px-3 py-1 rounded ${
              path?.startsWith(l.href)
                ? "bg-gray-700 text-white"
                : "text-gray-300 hover:text-white"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
