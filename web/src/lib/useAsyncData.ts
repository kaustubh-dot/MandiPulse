"use client";

import { useCallback, useEffect, useState } from "react";

export type AsyncDataState<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useAsyncData<T>(loader: () => Promise<T>) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<AsyncDataState<T>>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    void loader()
      .then((data) => {
        if (!cancelled) setState({ status: "success", data, error: null });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          data: null,
          error: error instanceof Error ? error.message : "Unable to load this data.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [loader, attempt]);

  const retry = useCallback(() => {
    // Event-driven reset: shows loading immediately and bumps attempt so the
    // effect refetches. The effect body itself never sets state synchronously.
    setState({ status: "loading", data: null, error: null });
    setAttempt((value) => value + 1);
  }, []);
  return { ...state, retry };
}
