import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { JSDOM } from "jsdom";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "https://mandipulse.test/recommend",
  pretendToBeVisual: true,
});

const { window } = dom;

function defineGlobal(name: string, value: unknown) {
  Object.defineProperty(globalThis, name, {
    value,
    configurable: true,
    writable: true,
  });
}

for (const key of [
  "window",
  "document",
  "DocumentFragment",
  "Element",
  "HTMLElement",
  "HTMLInputElement",
  "HTMLSelectElement",
  "HTMLTextAreaElement",
  "Node",
  "NodeList",
  "Event",
  "EventTarget",
  "CustomEvent",
  "KeyboardEvent",
  "MouseEvent",
  "MutationObserver",
  "getComputedStyle",
  "requestAnimationFrame",
  "cancelAnimationFrame",
  "localStorage",
  "sessionStorage",
  "SVGElement",
]) {
  const value = (window as unknown as Record<string, unknown>)[key];
  if (value !== undefined) defineGlobal(key, value);
}

defineGlobal("navigator", window.navigator);

defineGlobal("self", window);

class IntersectionObserverStub {
  observe(): void {}

  unobserve(): void {}

  disconnect(): void {}

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

if (!("IntersectionObserver" in window)) {
  defineGlobal(
    "IntersectionObserver",
    IntersectionObserverStub as unknown as typeof IntersectionObserver
  );
  window.IntersectionObserver =
    IntersectionObserverStub as unknown as typeof IntersectionObserver;
}

class ResizeObserverStub {
  private readonly callback: ResizeObserverCallback;

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }

  observe(target: Element) {
    const rect = { width: 1024, height: 480, top: 0, left: 0, x: 0, y: 0 };
    window.setTimeout(() => {
      this.callback(
        [
          {
            target,
            contentRect: { ...rect, bottom: rect.height, right: rect.width },
          } as unknown as ResizeObserverEntry,
        ],
        this as unknown as ResizeObserver
      );
    }, 0);
  }

  unobserve(): void {}

  disconnect(): void {}
}

if (!("ResizeObserver" in window)) {
  defineGlobal(
    "ResizeObserver",
    ResizeObserverStub as unknown as typeof ResizeObserver
  );
  window.ResizeObserver =
    ResizeObserverStub as unknown as typeof ResizeObserver;
}

const matchMediaStub = (query: string): MediaQueryList =>
  ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as MediaQueryList;

defineGlobal("matchMedia", matchMediaStub);
window.matchMedia = matchMediaStub;

if (!window.Element.prototype.scrollIntoView) {
  window.Element.prototype.scrollIntoView = () => {};
}

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;

export const FIXTURE_DIR = resolve(__dirname, "../public/data");

export function loadFixture<T>(name: string): T {
  return JSON.parse(readFileSync(resolve(FIXTURE_DIR, name), "utf8")) as T;
}

export interface FetchRoute {
  status?: number;
  body: unknown;
}

export function installFetchRoutes(routes: Record<string, FetchRoute>): string[] {
  const calls: string[] = [];
  const fetchMock = (async (input: RequestInfo | URL) => {
    const raw = typeof input === "string" ? input : String(input);
    const path = raw.replace(/^https?:\/\/[^/]+/, "");
    calls.push(path);
    const route = routes[path];
    if (!route) {
      return {
        ok: false,
        status: 404,
        text: async () => "Not Found",
      } as Response;
    }
    const status = route.status ?? 200;
    return {
      ok: status >= 200 && status < 300,
      status,
      text: async () =>
        typeof route.body === "string"
          ? route.body
          : JSON.stringify(route.body),
    } as Response;
  }) as typeof fetch;
  defineGlobal("fetch", fetchMock);
  window.fetch = fetchMock;
  return calls;
}
