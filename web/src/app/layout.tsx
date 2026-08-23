import type { Metadata } from "next";
import { Barlow_Condensed, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";
import AppShell from "@/components/shell/AppShell";

const barlowCondensed = Barlow_Condensed({
  subsets: ["latin"],
  weight: "700",
  variable: "--font-barlow",
  display: "swap",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-plex-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["500", "600"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MandiPulse India",
  description:
    "Transport-cost-aware mandi decision intelligence for Maharashtra onion farmers.",
};

// Applies the persisted or system theme before first paint to avoid a flash.
const themeInitScript = `(function(){try{var s=localStorage.getItem("mp-theme");var m=window.matchMedia("(prefers-color-scheme: dark)").matches;var t=s||(m?"dark":"light");document.documentElement.setAttribute("data-theme",t);}catch(e){}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      data-theme="light"
      className={`${barlowCondensed.variable} ${plexSans.variable} ${plexMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-dvh">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[400] focus:rounded-control focus:border focus:border-rule-strong focus:bg-surface-raised focus:px-4 focus:py-2 focus:text-sm focus:text-ink"
        >
          Skip to main content
        </a>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
