import type { RadarData } from "../types";

const base = `${import.meta.env.BASE_URL}data`;

type LoadOptions = {
  cacheBust?: boolean;
};

async function json<T>(name: string, options: LoadOptions = {}): Promise<T> {
  const suffix = options.cacheBust ? `?t=${Date.now()}` : "";
  const response = await fetch(`${base}/${name}.json${suffix}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`无法加载 ${name}.json`);
  return response.json() as Promise<T>;
}

export async function loadRadarData(options: LoadOptions = {}): Promise<RadarData> {
  const [matches, predictions, scores, odds, upsets, divergences, accuracy, reviews, backtest, metadata, intelligence] =
    await Promise.all([
      json<RadarData["matches"]>("matches", options),
      json<RadarData["predictions"]>("predictions", options),
      json<RadarData["scores"]>("score_probabilities", options),
      json<RadarData["odds"]>("odds_movements", options),
      json<RadarData["upsets"]>("upset_radar", options),
      json<RadarData["divergences"]>("model_divergence", options),
      json<RadarData["accuracy"]>("accuracy_metrics", options),
      json<RadarData["reviews"]>("review", options),
      json<RadarData["backtest"]>("backtest", options),
      json<RadarData["metadata"]>("data_metadata", options),
      json<RadarData["intelligence"]>("match_intelligence", options),
    ]);
  return { matches, predictions, scores, odds, upsets, divergences, accuracy, reviews, backtest, metadata, intelligence };
}
