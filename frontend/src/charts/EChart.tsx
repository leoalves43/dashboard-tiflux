import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";
import { useEffect, useRef } from "react";

// Register only what the dashboard draws; the full bundle is ~3x larger.
echarts.use([BarChart, LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

export type ChartOption = EChartsOption;

interface Props {
  option: ChartOption;
  className?: string;
  ariaLabel: string;
  onItemClick?: (dataIndex: number) => void;
}

/** Owns one ECharts instance; resizes with its container. */
export function EChart({ option, className = "chart", ariaLabel, onItemClick }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!hostRef.current) return;
    const chart = echarts.init(hostRef.current, undefined, { renderer: "canvas" });
    chartRef.current = chart;
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(hostRef.current);
    return () => {
      observer.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    chartRef.current?.setOption(option, { notMerge: true });
  }, [option]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !onItemClick) return;
    const handle = (params: { dataIndex?: number }) => {
      if (params.dataIndex !== undefined) onItemClick(params.dataIndex);
    };
    chart.on("click", handle);
    return () => { chart.off("click", handle); };
  }, [onItemClick]);

  return <div ref={hostRef} className={className} role="img" aria-label={ariaLabel} />;
}
