export type Outcome = "home" | "draw" | "away";
export type Confidence = "high" | "medium" | "low";

export interface Team {
  code: string;
  name: string;
  english_name: string;
  flag: string;
  elo: number;
  form: string[];
}

export interface Match {
  match_id: string;
  match_no: number;
  stage: string;
  round: number;
  group_name: string;
  home_team: Team;
  away_team: Team;
  match_time: string;
  stadium: string;
  city: string;
  status: "scheduled" | "live" | "finished";
  home_score: number | null;
  away_score: number | null;
  minute?: number;
}

export interface Prediction {
  match_id: string;
  model_home_win_prob: number;
  model_draw_prob: number;
  model_away_win_prob: number;
  market_home_win_prob: number;
  market_draw_prob: number;
  market_away_win_prob: number;
  final_home_win_prob: number;
  final_draw_prob: number;
  final_away_win_prob: number;
  expected_home_goals: number;
  expected_away_goals: number;
  over_25_prob: number;
  under_25_prob: number;
  btts_prob: number;
  upset_index: number;
  confidence_level: Confidence;
  prediction_label: string;
  summary: string;
  factors: string[];
  updated_at: string;
}

export interface ScoreProbability {
  match_id: string;
  scores: Array<{ score: string; probability: number }>;
}

export interface OddsMovement {
  match_id: string;
  market_type: string;
  selection: Outcome;
  open_odds: number;
  current_odds: number;
  open_probability: number;
  current_probability: number;
  change_24h: number;
  change_6h: number;
  change_1h: number;
  bookmaker_consensus: number;
  market_dispersion: number;
  signal: string;
  risk_note: string;
  history: Array<{ time: string; home: number; draw: number; away: number }>;
}

export interface UpsetRadar {
  match_id: string;
  upset_index: number;
  risk_level: string;
  favorite_team: string;
  underdog_team: string;
  favorite_overheat_score: number;
  underdog_not_lose_prob: number;
  draw_heat_score: number;
  reason: string[];
}

export interface Divergence {
  match_id: string;
  home_divergence: number;
  draw_divergence: number;
  away_divergence: number;
  largest_divergence_selection: Outcome;
  largest_divergence_value: number;
  divergence_level: string;
  summary: string;
}

export interface AccuracyMetrics {
  overall: {
    matches_reviewed: number;
    result_accuracy: number;
    over_under_accuracy: number;
    top5_score_hit_rate: number;
    upset_warning_hit_rate: number;
    brier_score: number;
    log_loss: number;
  };
  by_stage: Array<{ stage: string; matches: number; result_accuracy: number; brier_score: number }>;
  by_confidence: Array<{ confidence_level: Confidence; matches: number; result_accuracy: number }>;
  calibration: Array<{ predicted: number; actual: number }>;
}

export interface Review {
  match_id: string;
  actual_result: Outcome;
  predicted_result: Outcome;
  result_hit: boolean;
  over_under_hit: boolean;
  score_top5_hit: boolean;
  upset_warning_hit: boolean;
  brier_score: number;
  log_loss: number;
  model_error_summary: string;
  odds_signal_review: string;
  adjustment_suggestion: string;
}

export interface BacktestRow {
  model: string;
  matches: number;
  accuracy: number;
  brier_score: number;
  log_loss: number;
  lift: number;
}

export interface DataMetadata {
  source: string;
  source_label: string;
  source_url: string;
  generated_at: string;
  update_frequency: string;
  fixtures_total: number;
  finished_total: number;
  live_total: number;
  odds_mode: string;
  odds_notice: string;
}

export interface RadarData {
  matches: Match[];
  predictions: Prediction[];
  scores: ScoreProbability[];
  odds: OddsMovement[];
  upsets: UpsetRadar[];
  divergences: Divergence[];
  accuracy: AccuracyMetrics;
  reviews: Review[];
  backtest: BacktestRow[];
  metadata: DataMetadata;
}
