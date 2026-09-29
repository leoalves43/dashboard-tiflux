import { useEffect, useState } from "react";

export interface FetchState<T> {
  data: T | undefined;
  error: string | undefined;
  loading: boolean;
}

/**
 * Runs `load` whenever `key` changes, aborting the previous request.
 * Previous data stays visible while reloading (charts dim instead of flashing).
 * Example: const kpis = useFetch((s) => api.kpis(filters, s), JSON.stringify(filters));
 */
export function useFetch<T>(load: (signal: AbortSignal) => Promise<T>, key: string): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({ data: undefined, error: undefined, loading: true });

  useEffect(() => {
    const controller = new AbortController();
    setState((prev) => ({ ...prev, loading: true, error: undefined }));
    load(controller.signal)
      .then((data) => setState({ data, error: undefined, loading: false }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState((prev) => ({ ...prev, error: String(error), loading: false }));
      });
    return () => controller.abort();
    // `key` captures every input of `load`; listing `load` would refetch on each render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return state;
}
