import type { Confidence, Outcome } from "../types";

export const pct = (value: number, digits = 0) => `${(value * 100).toFixed(digits)}%`;
export const signedPct = (value: number) => `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
export const outcomeLabel: Record<Outcome, string> = { home: "主胜", draw: "平局", away: "客胜" };
export const confidenceLabel: Record<Confidence, string> = { high: "高信心", medium: "中信心", low: "低信心" };

export function formatMatchTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Shanghai",
  }).format(new Date(value));
}

export function riskTone(score: number) {
  if (score >= 76) return "danger";
  if (score >= 56) return "warning";
  if (score >= 31) return "notice";
  return "safe";
}
