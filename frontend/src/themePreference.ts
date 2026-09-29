export type ThemeChoice = "light" | "dark" | "system";
const THEME_KEY = "dashboard-theme";

export function readStoredTheme(): ThemeChoice {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

/** Sets data-theme on <html>; called before the first render so charts read the right tokens. */
export function applyTheme(choice: ThemeChoice): void {
  if (choice === "system") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", choice);
  try { localStorage.setItem(THEME_KEY, choice); } catch { /* private mode: choice just won't persist */ }
}
