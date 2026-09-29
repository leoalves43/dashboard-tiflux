import { useEffect, useState } from "react";

/** Resolved token values charts need (ECharts draws on canvas, so CSS vars must be read in JS). */
export interface ChartTheme {
  surface: string;
  ink1: string;
  ink2: string;
  ink3: string;
  grid: string;
  axis: string;
  series: string[];
  ordinal: string[];
  good: string;
  serious: string;
  critical: string;
  font: string;
}

function token(style: CSSStyleDeclaration, name: string): string {
  return style.getPropertyValue(name).trim();
}

export function readChartTheme(root: HTMLElement = document.documentElement): ChartTheme {
  const style = getComputedStyle(root);
  const read = (name: string) => token(style, name);
  return {
    surface: read("--surface"),
    ink1: read("--ink-1"),
    ink2: read("--ink-2"),
    ink3: read("--ink-3"),
    grid: read("--grid"),
    axis: read("--axis"),
    series: [1, 2, 3, 4, 5, 6, 7, 8].map((i) => read(`--series-${i}`)),
    ordinal: [1, 2, 3, 4, 5].map((i) => read(`--ord-${i}`)),
    good: read("--good"),
    serious: read("--serious"),
    critical: read("--critical"),
    font: read("--font"),
  };
}

/** Re-reads tokens when the OS scheme or the data-theme toggle changes. */
export function useChartTheme(): ChartTheme {
  const [theme, setTheme] = useState<ChartTheme>(() => readChartTheme());
  useEffect(() => {
    const refresh = () => setTheme(readChartTheme());
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", refresh);
    const observer = new MutationObserver(refresh);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      media.removeEventListener("change", refresh);
      observer.disconnect();
    };
  }, []);
  return theme;
}
