import type { RadarData } from "../types";

const base = `${import.meta.env.BASE_URL}data`;

async function json<T>(name: string): Promise<T> {
  const response = await fetch(`${base}/${name}.json`);
  if (!response.ok) throw new Error(`无法加载 ${name}.json`);
  return response.json() as Promise<T>;
}

export async function loadRadarData(): Promise<RadarData> {
  const [matches, predictions, scores, odds, upsets, divergences, accuracy, reviews, backtest, metadata, intelligence] =
    await Promise.all([
      json<RadarData["matches"]>("matches"),
      json<RadarData["predictions"]>("predictions"),
      json<RadarData["scores"]>("score_probabilities"),
      json<RadarData["odds"]>("odds_movements"),
      json<RadarData["upsets"]>("upset_radar"),
      json<RadarData["divergences"]>("model_divergence"),
      json<RadarData["accuracy"]>("accuracy_metrics"),
      json<RadarData["reviews"]>("review"),
      json<RadarData["backtest"]>("backtest"),
      json<RadarData["metadata"]>("data_metadata"),
      json<RadarData["intelligence"]>("match_intelligence"),
    ]);
  return { matches, predictions, scores, odds, upsets, divergences, accuracy, reviews, backtest, metadata, intelligence };
}
