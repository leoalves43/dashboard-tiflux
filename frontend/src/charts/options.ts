import type { ChartOption } from "./EChart";
import type { ChartTheme } from "./theme";

export interface BarSeries {
  name: string;
  color: string;
  values: number[];
}

const intFormat = new Intl.NumberFormat("pt-BR");
const BAR_MAX_WIDTH = 24;
const BAR_RADIUS_H: [number, number, number, number] = [0, 4, 4, 0]; // rounded data end, square baseline
const BAR_RADIUS_V: [number, number, number, number] = [4, 4, 0, 0];

const AREA_TOP_ALPHA = 0.25;

/** "#rrggbb" + alpha -> "rgba(...)"; tokens are hex, ECharts gradients need per-stop alpha. Example: withAlpha("#2a78d6", 0.25) */
export function withAlpha(hex: string, alpha: number): string {
  const match = /^#([0-9a-f]{6})$/i.exec(hex);
  if (!match) throw new Error(`withAlpha: color=${JSON.stringify(hex)}; expected "#rrggbb"`);
  const value = parseInt(match[1], 16);
  return `rgba(${value >> 16}, ${(value >> 8) & 255}, ${value & 255}, ${alpha})`;
}

/** Vertical fade under a line: tone at 25% on top, transparent at the baseline. */
function areaGradient(color: string) {
  return {
    type: "linear" as const, x: 0, y: 0, x2: 0, y2: 1,
    colorStops: [{ offset: 0, color: withAlpha(color, AREA_TOP_ALPHA) }, { offset: 1, color: withAlpha(color, 0) }],
  };
}

function baseOption(theme: ChartTheme): ChartOption {
  return {
    backgroundColor: "transparent",
    textStyle: { fontFamily: theme.font, color: theme.ink2 },
    animationDuration: 300,
    tooltip: {
      backgroundColor: theme.surface,
      borderColor: theme.grid,
      textStyle: { color: theme.ink1, fontFamily: theme.font },
      valueFormatter: (value) => intFormat.format(Number(value)),
    },
    legend: { top: 0, left: 0, icon: "roundRect", itemWidth: 12, itemHeight: 8, textStyle: { color: theme.ink2 } },
  };
}

function valueAxis(theme: ChartTheme) {
  return {
    type: "value" as const,
    axisLabel: { color: theme.ink3, formatter: (v: number) => intFormat.format(v) },
    splitLine: { lineStyle: { color: theme.grid, width: 1, type: "solid" as const } },
  };
}

function categoryAxis(theme: ChartTheme, labels: string[], truncate = 0) {
  return {
    type: "category" as const,
    data: labels,
    axisLine: { lineStyle: { color: theme.axis } },
    axisTick: { show: false },
    axisLabel: {
      color: theme.ink2,
      formatter: (v: string) => (truncate && v.length > truncate ? `${v.slice(0, truncate - 1)}…` : v),
    },
  };
}

/** Horizontal grouped bars for rankings (labels on the y axis, longest first at the top). */
export function horizontalBars(theme: ChartTheme, labels: string[], series: BarSeries[]): ChartOption {
  return {
    ...baseOption(theme),
    legend: series.length > 1 ? baseOption(theme).legend : { show: false },
    tooltip: { ...baseOption(theme).tooltip, trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 8, right: 24, top: series.length > 1 ? 28 : 8, bottom: 8, containLabel: true },
    xAxis: valueAxis(theme),
    yAxis: { ...categoryAxis(theme, labels, 32), inverse: true },
    series: series.map((s) => ({
      type: "bar", name: s.name, data: s.values, barMaxWidth: BAR_MAX_WIDTH, barGap: "15%",
      itemStyle: { color: s.color, borderRadius: BAR_RADIUS_H },
    })),
  };
}

/** Vertical columns; `colors` per bar is for ordinal buckets (one ramp step per bucket). */
export function columns(theme: ChartTheme, labels: string[], values: number[], colors: string[], name: string): ChartOption {
  return {
    ...baseOption(theme),
    legend: { show: false },
    tooltip: { ...baseOption(theme).tooltip, trigger: "item" },
    grid: { left: 8, right: 8, top: 24, bottom: 8, containLabel: true },
    xAxis: categoryAxis(theme, labels),
    yAxis: valueAxis(theme),
    series: [{
      type: "bar", name, barMaxWidth: BAR_MAX_WIDTH * 2,
      data: values.map((value, i) => ({ value, itemStyle: { color: colors[i % colors.length], borderRadius: BAR_RADIUS_V } })),
      label: { show: true, position: "top", color: theme.ink2, formatter: (p) => intFormat.format(Number(p.value)) },
    }],
  };
}

/** Lines over time with a crosshair tooltip listing every series. */
export function timeLines(theme: ChartTheme, periods: string[], series: BarSeries[]): ChartOption {
  return {
    ...baseOption(theme),
    tooltip: { ...baseOption(theme).tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: theme.axis } } },
    grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
    xAxis: { ...categoryAxis(theme, periods), boundaryGap: false },
    yAxis: valueAxis(theme),
    series: series.map((s) => ({
      type: "line", name: s.name, data: s.values, showSymbol: periods.length <= 40, symbolSize: 8,
      lineStyle: { width: 2, color: s.color }, itemStyle: { color: s.color, borderColor: theme.surface, borderWidth: 2 },
      areaStyle: { color: areaGradient(s.color) },
    })),
  };
}
