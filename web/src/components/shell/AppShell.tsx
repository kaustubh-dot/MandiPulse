"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/recommend", label: "Decision" },
  { href: "/forecast", label: "Forecast" },
  { href: "/coverage", label: "Coverage" },
];

const SNAPSHOT_LABEL = "Snapshot 30 Oct 2025";

type Theme = "light" | "dark";

const THEME_ATTR = "data-theme";

function subscribeToTheme(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: [THEME_ATTR],
  });
  return () => observer.disconnect();
}

function getThemeSnapshot(): Theme {
  return document.documentElement.getAttribute(THEME_ATTR) === "dark"
    ? "dark"
    : "light";
}

function getThemeServerSnapshot(): Theme {
  return "light";
}

function ThemeToggle() {
  // Theme is owned by the <html> attribute (external store); subscribing via
  // useSyncExternalStore avoids setState-in-effect and hydration mismatches.
  const theme = useSyncExternalStore(
    subscribeToTheme,
    getThemeSnapshot,
    getThemeServerSnapshot
  );

  function applyTheme(next: Theme) {
    document.documentElement.setAttribute(THEME_ATTR, next);
    try {
      localStorage.setItem("mp-theme", next);
    } catch {
      // Storage may be unavailable; theme still applies for this visit.
    }
  }

  return (
    <button
      type="button"
      onClick={() => applyTheme(theme === "dark" ? "light" : "dark")}
      aria-pressed={theme === "dark"}
      className="flex h-12 w-full items-center justify-between border border-rule bg-paper px-3 text-sm text-ink-2 motion-safe-transition hover:border-rule-strong hover:text-ink aria-pressed:border-rule-strong aria-pressed:bg-surface aria-pressed:text-ink"
    >
      <span>{theme === "dark" ? "Dark" : "Light"} theme</span>
      <span aria-hidden="true" className="numeric text-xs">
        {theme === "dark" ? "D" : "L"}
      </span>
    </button>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const rawPathname = usePathname();
  const pathname =
    rawPathname !== "/" && rawPathname.endsWith("/")
      ? rawPathname.slice(0, -1)
      : rawPathname;
  return (
    <nav aria-label="Primary">
      <ul className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-12 items-center gap-2 border-l-2 px-3 py-3 text-sm font-medium motion-safe-transition ${
                  active
                    ? "border-accent text-ink"
                    : "border-transparent text-ink-2 hover:border-rule-strong hover:text-ink"
                }`}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function RailContent() {
  return (
    <div className="flex h-full flex-col gap-6 px-4 py-5">
      <Link href="/" className="block rounded-control">
        <span className="font-display text-[1.75rem] leading-none text-ink">
          MandiPulse
        </span>
        <span className="mt-1 block text-xs font-body text-muted">
          Mandi decision intelligence
        </span>
      </Link>

      <NavLinks />

      <div className="mt-auto flex flex-col gap-4">
        <p className="numeric text-xs text-muted">{SNAPSHOT_LABEL}</p>
        <details className="text-sm text-ink-2">
          <summary className="min-h-12 cursor-pointer leading-[3rem] hover:text-ink">
            Method &amp; assumptions
          </summary>
          <div className="flex flex-col gap-2 pb-2 text-xs leading-relaxed text-muted">
            <p>
              Ranking is transport-adjusted: expected net price after estimated
              transport cost. Uncertainty stays separate evidence.
            </p>
            <Link href="/#method" className="underline hover:text-ink">
              Read the method summary
            </Link>
          </div>
        </details>
        <ThemeToggle />
      </div>
    </div>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [sheetOpen, setSheetOpen] = useState(false);
  const sheetRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const bodyOverflowRef = useRef("");

  useEffect(() => {
    if (!sheetOpen) return;
    const sheet = sheetRef.current;
    const menuButton = menuButtonRef.current;
    bodyOverflowRef.current = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const focusFirstItem = () => {
      sheet
        ?.querySelector<HTMLElement>("a[href], button:not([disabled])")
        ?.focus();
    };

    focusFirstItem();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setSheetOpen(false);
        return;
      }
      if (event.key !== "Tab" || !sheet) {
        return;
      }
      const focusables = Array.from(
        sheet.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
      );
      if (focusables.length === 0) {
        event.preventDefault();
        sheet.focus();
        return;
      }
      const first = focusables[0]!;
      const last = focusables[focusables.length - 1]!;
      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
        return;
      }
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = bodyOverflowRef.current;
      menuButton?.focus();
    };
  }, [sheetOpen]);

  return (
    <div className="min-h-dvh">
      {/* Desktop decision rail */}
      <aside className="fixed inset-y-0 left-0 z-10 hidden w-60 border-r border-rule bg-paper-2 shadow-none lg:block">
        <RailContent />
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-rule bg-paper-2 px-4 py-3 lg:hidden">
        <Link href="/" className="font-display text-xl leading-none text-ink">
          MandiPulse
        </Link>
        <div className="flex items-center gap-3">
          <span className="numeric whitespace-nowrap text-xs text-muted">
            {SNAPSHOT_LABEL}
          </span>
          <button
            ref={menuButtonRef}
            type="button"
            aria-expanded={sheetOpen}
            aria-controls="mobile-nav-sheet"
            onClick={() => setSheetOpen((open) => !open)}
            className="min-h-12 whitespace-nowrap border border-rule bg-paper px-3 text-sm text-ink motion-safe-transition hover:border-rule-strong"
          >
            Menu
          </button>
        </div>
      </header>

      {/* Mobile navigation sheet */}
      {sheetOpen ? (
        <div
          id="mobile-nav-sheet"
          ref={sheetRef}
          role="dialog"
          aria-modal="true"
          aria-label="Navigation"
          tabIndex={-1}
          className="fixed inset-x-0 top-[57px] bottom-0 z-50 flex flex-col gap-5 overflow-y-auto border-t border-rule-strong bg-paper px-4 pb-4 pt-5 lg:hidden"
        >
          <div className="border-b border-rule pb-3">
            <h2 className="font-display text-[2rem] leading-none text-ink">
              Navigation
            </h2>
          </div>
          <NavLinks onNavigate={() => setSheetOpen(false)} />
          <div className="pt-1">
            <ThemeToggle />
          </div>
        </div>
      ) : null}

      {/* Main canvas */}
      <div className="lg:pl-60">
        <main
          id="main-content"
          className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8"
        >
          {children}
        </main>
        <footer className="border-t border-rule px-4 py-4 sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted">
            <span>MandiPulse</span>
            <span className="numeric">{SNAPSHOT_LABEL}</span>
            <span>Frozen demonstration data</span>
            <Link href="/#method" className="underline hover:text-ink">
              Method
            </Link>
            <Link href="/coverage" className="underline hover:text-ink">
              Coverage provenance
            </Link>
          </div>
        </footer>
      </div>
    </div>
  );
}
