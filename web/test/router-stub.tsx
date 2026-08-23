import type { ReactElement, ReactNode } from "react";
import { useMemo } from "react";
import { render } from "@testing-library/react";
import { AppRouterContext } from "next/dist/shared/lib/app-router-context.shared-runtime.js";
import {
  PathnameContext,
  SearchParamsContext,
  ReadonlyURLSearchParams,
} from "next/dist/shared/lib/hooks-client-context.shared-runtime.js";

interface RouterStubOptions {
  pathname?: string;
  search?: string;
}

function NextStubProviders({
  pathname = "/",
  search = "",
  children,
}: RouterStubOptions & { children: ReactNode }) {
  const router = useMemo(
    () => ({
      push: () => {},
      replace: () => {},
      prefetch: () => {},
      back: () => {},
      forward: () => {},
      refresh: () => {},
      bfcacheId: "test-stub",
    }),
    []
  );
  const searchParams = useMemo(() => new ReadonlyURLSearchParams(search), [search]);
  return (
    <AppRouterContext.Provider value={router}>
      <PathnameContext.Provider value={pathname}>
        <SearchParamsContext.Provider value={searchParams}>
          {children}
        </SearchParamsContext.Provider>
      </PathnameContext.Provider>
    </AppRouterContext.Provider>
  );
}

export function renderWithRouter(
  ui: ReactElement,
  options: RouterStubOptions = {}
) {
  return render(<NextStubProviders {...options}>{ui}</NextStubProviders>);
}
