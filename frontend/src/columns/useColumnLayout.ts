import { useCallback, useState } from "react";
import { type ColumnLayout, type LayoutStorage, loadLayout, saveLayout } from "./columnLayout";

/** window.localStorage, or undefined where merely touching it throws (blocked site data). */
export function browserStorage(): LayoutStorage | undefined {
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

/**
 * Column layout state persisted on every change. Read once per mount, so all ticket tables share it.
 * Example: const { layout, setLayout, reset } = useColumnLayout(DEFAULT_TICKET_LAYOUT, browserStorage());
 */
export function useColumnLayout(defaults: ColumnLayout, storage: LayoutStorage | undefined) {
  const [layout, setState] = useState<ColumnLayout>(() => loadLayout(storage, defaults));
  const setLayout = useCallback((next: ColumnLayout) => {
    setState(next);
    saveLayout(storage, next);
  }, [storage]);
  const reset = useCallback(() => setLayout(defaults), [setLayout, defaults]);
  return { layout, setLayout, reset };
}
