export interface DatePreset {
  id: string;
  label: string;
  range: (today: Date) => [string, string];
}

/** Local calendar date as YYYY-MM-DD (toISOString would shift to UTC). */
export function isoDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function daysAgo(today: Date, days: number): Date {
  const copy = new Date(today);
  copy.setDate(copy.getDate() - days);
  return copy;
}

export const DATE_PRESETS: DatePreset[] = [
  { id: "all", label: "Todo o período", range: () => ["", ""] },
  { id: "7d", label: "Últimos 7 dias", range: (t) => [isoDate(daysAgo(t, 6)), isoDate(t)] },
  { id: "30d", label: "Últimos 30 dias", range: (t) => [isoDate(daysAgo(t, 29)), isoDate(t)] },
  { id: "90d", label: "Últimos 90 dias", range: (t) => [isoDate(daysAgo(t, 89)), isoDate(t)] },
  { id: "mtd", label: "Este mês", range: (t) => [isoDate(new Date(t.getFullYear(), t.getMonth(), 1)), isoDate(t)] },
  { id: "12m", label: "Últimos 12 meses", range: (t) => [isoDate(daysAgo(t, 364)), isoDate(t)] },
  { id: "ytd", label: "Este ano", range: (t) => [isoDate(new Date(t.getFullYear(), 0, 1)), isoDate(t)] },
];

/** Which preset matches the current range, or "custom". */
export function matchPreset(from: string, to: string, today: Date = new Date()): string {
  const found = DATE_PRESETS.find((preset) => {
    const [presetFrom, presetTo] = preset.range(today);
    return presetFrom === from && presetTo === to;
  });
  return found ? found.id : "custom";
}
