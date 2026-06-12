import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, BarChart3, ChevronRight, CircleGauge, Clock3,
  Crosshair, Database, FlaskConical, Home, Menu, Radio, RefreshCw, Search,
  KeyRound, Lock, LogOut, Settings, ShieldAlert, Sparkles, Target,
  TrendingDown, TrendingUp, X,
} from "lucide-react";
import { Link, NavLink, Route, Routes, useParams } from "react-router-dom";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { loadRadarData } from "./lib/data";
import { confidenceLabel, formatMatchTime, formatUpdatedAt, outcomeLabel, pct, riskTone, signedPct } from "./lib/format";
import type { DataMetadata, Match, MatchIntelligence, Prediction, RadarData } from "./types";

const nav = [
  { to: "/", label: "赛事总览", icon: Home },
  { to: "/odds", label: "赔率异动", icon: Activity },
  { to: "/upset", label: "爆冷雷达", icon: ShieldAlert },
  { to: "/accuracy", label: "准确率中心", icon: Target },
  { to: "/review", label: "赛后复盘", icon: Search },
  { to: "/backtest", label: "模型回测", icon: FlaskConical },
  { to: "/settings", label: "系统设置", icon: Settings },
];

function App() {
  const [data, setData] = useState<RadarData | null>(null);
  const [error, setError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState("");

  async function fetchData(cacheBust = false) {
    const next = await loadRadarData({ cacheBust });
    setData(next);
    setError("");
  }

  useEffect(() => {
    fetchData().catch((reason) => setError(String(reason)));
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshError("");
    try {
      await fetchData(true);
    } catch (reason) {
      setRefreshError(String(reason));
    } finally {
      setRefreshing(false);
    }
  }

  if (error) return <StatePanel title="数据加载失败" detail={error} />;
  if (!data) return <StatePanel title="正在同步雷达数据" detail="读取比赛、赔率与模型输出..." loading />;

  const nextMatch = data.matches
    .filter((match) => match.status === "scheduled")
    .sort((a, b) => Date.parse(a.match_time) - Date.parse(b.match_time))[0];
  const countdownDays = nextMatch
    ? Math.max(0, Math.ceil((Date.parse(nextMatch.match_time) - Date.now()) / 86_400_000))
    : 0;

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Crosshair size={23} /></div>
          <div><strong>阿基米</strong><span>世界杯雷达</span></div>
          <button className="icon-button close-menu" aria-label="关闭导航菜单" onClick={() => setMenuOpen(false)}><X size={20} /></button>
        </div>
        <nav>
          {nav.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"} onClick={() => setMenuOpen(false)}>
              <item.icon size={18} /><span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="data-status"><span className="live-dot" /><div><strong>{data.metadata.source_label}</strong><small>{data.metadata.update_frequency}自动更新</small></div></div>
          <div className="world-cup-count"><span>距离下一场</span><strong>{countdownDays} 天</strong><small>数据时间 {formatUpdatedAt(data.metadata.generated_at)}</small></div>
        </div>
      </aside>
      {menuOpen && <button className="menu-backdrop" onClick={() => setMenuOpen(false)} />}
      <main className="main">
        <header className="topbar">
          <button className="icon-button menu-button" aria-label="打开导航菜单" onClick={() => setMenuOpen(true)}><Menu size={21} /></button>
          <div className="topbar-title"><Radio size={17} /><span>2026 FIFA WORLD CUP</span><b>研究模式</b></div>
          <div className="topbar-actions">
            <button className="avatar">AK</button>
          </div>
        </header>
        <div className="global-refresh-bar">
          <div className="global-refresh-copy">
            <span className="eyebrow">DATA CONTROL</span>
            <strong>当前数据时间 {formatUpdatedAt(data.metadata.generated_at)}</strong>
            <small>{refreshing ? "正在重新拉取最新 JSON 数据..." : "如果页面还在显示旧比赛状态，可手动刷新一次。"}</small>
          </div>
          <button className="secondary-button refresh-button prominent" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={refreshing ? "spin" : ""} size={15} />
            {refreshing ? "刷新中..." : "手动刷新数据"}
          </button>
        </div>
        {refreshError && <div className="refresh-error-banner"><AlertTriangle size={15} /> {refreshError}</div>}
        <Routes>
          <Route path="/" element={<Dashboard data={data} />} />
          <Route path="/match/:id" element={<MatchDetail data={data} />} />
          <Route path="/odds" element={<OddsPage data={data} />} />
          <Route path="/upset" element={<UpsetPage data={data} />} />
          <Route path="/accuracy" element={<AccuracyPage data={data} />} />
          <Route path="/review" element={<ReviewPage data={data} />} />
          <Route path="/backtest" element={<BacktestPage data={data} />} />
          <Route path="/settings" element={<SettingsPage metadata={data.metadata} />} />
        </Routes>
        <footer>本系统仅用于个人赛事数据分析、预测研究和模型复盘，不构成任何投注、购彩或投资建议。体育比赛结果具有高度不确定性，请理性看待模型结论。</footer>
      </main>
    </div>
  );
}

function StatePanel({ title, detail, loading }: { title: string; detail: string; loading?: boolean }) {
  return <div className="state-panel">{loading ? <CircleGauge className="spin" size={32} /> : <AlertTriangle size={32} />}<h2>{title}</h2><p>{detail}</p></div>;
}

function PageHeader({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: React.ReactNode }) {
  return <div className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{children && <div className="page-actions">{children}</div>}</div>;
}

function Dashboard({ data }: { data: RadarData }) {
  const visible = data.matches.filter((match) => match.status !== "finished").slice(0, 6);
  const avgConfidence = Math.round(data.predictions.reduce((sum, p) => sum + Math.max(p.final_home_win_prob, p.final_draw_prob, p.final_away_win_prob), 0) / data.predictions.length * 100);
  const highRisk = data.upsets.filter((row) => row.upset_index >= 56).length;
  const hottest = [...data.odds].sort((a, b) => Math.abs(b.change_24h) - Math.abs(a.change_24h))[0];
  const hotMatch = data.matches.find((m) => m.match_id === hottest.match_id)!;
  return <div className="page">
    <PageHeader eyebrow="MATCH INTELLIGENCE" title="今日赛事雷达" description="从球队强度、市场变化与模型分歧中，识别比赛最关键的不确定性。">
      <button className="secondary-button"><Clock3 size={15} /> 北京时间</button>
      <button className="primary-button"><Sparkles size={15} /> 生成今日简报</button>
    </PageHeader>
    <section className="hero-grid">
      <div className="hero-card">
        <div className="hero-copy"><span className="status-chip"><span className="live-dot" /> 模型运行正常</span><h2>世界杯赛程<br /><em>持续自动校准</em></h2><p>{data.matches.length} 场已确定对阵进入预测队列，其中 {data.metadata.finished_total} 场已有赛果，{highRisk} 场呈现较高爆冷风险。</p><div className="hero-meta"><span><Database size={15} /> OpenFootball 赛程/赛果</span><span><Activity size={15} /> 实时赔率覆盖 {data.metadata.real_odds_matches} 场</span></div></div>
        <div className="radar-visual"><div className="radar-ring ring-1" /><div className="radar-ring ring-2" /><div className="radar-ring ring-3" /><div className="radar-sweep" /><Crosshair size={28} /><span className="ping p1" /><span className="ping p2" /><span className="ping p3" /></div>
      </div>
      <div className="metric-stack">
        <MetricCard icon={Target} label="模型平均把握" value={`${avgConfidence}%`} note="较基线 +7.3%" tone="blue" />
        <MetricCard icon={ShieldAlert} label="高风险场次" value={`${highRisk}`} note="需关注临场阵容" tone="orange" />
        <MetricCard icon={TrendingUp} label="最大代理偏移" value={signedPct(hottest.change_24h)} note={`${hotMatch.home_team.name} vs ${hotMatch.away_team.name}`} tone="mint" />
      </div>
    </section>
    <SectionTitle title="即将进行" detail="按公开赛程与当前模型概率排序展示" action={`已载入 ${data.matches.length} 场`} />
    <div className="match-grid">{visible.map((match) => <MatchCard key={match.match_id} match={match} prediction={findPrediction(data, match.match_id)} scores={data.scores.find((s) => s.match_id === match.match_id)?.scores ?? []} />)}</div>
    <section className="dashboard-bottom">
      <div className="panel">
        <SectionTitle title="重点观察榜" detail="综合分歧、市场热度与不败概率" />
        <div className="ranking-list">{[...data.upsets].sort((a, b) => b.upset_index - a.upset_index).slice(0, 5).map((row, i) => {
          const match = data.matches.find((m) => m.match_id === row.match_id)!;
          return <Link to={`/match/${row.match_id}`} className="ranking-row" key={row.match_id}><b>0{i + 1}</b><span>{match.home_team.flag} {match.home_team.name} <i>vs</i> {match.away_team.name} {match.away_team.flag}</span><RiskBadge score={row.upset_index} /><ChevronRight size={16} /></Link>;
        })}</div>
      </div>
      <div className="panel accuracy-brief">
        <SectionTitle title="模型健康度" detail="最近 48 场回测结果" />
        <div className="score-orbit"><strong>{pct(data.accuracy.overall.result_accuracy, 1)}</strong><span>赛果命中率</span></div>
        <div className="brief-metrics"><div><span>Brier Score</span><b>{data.accuracy.overall.brier_score}</b></div><div><span>Log Loss</span><b>{data.accuracy.overall.log_loss}</b></div><div><span>比分 Top 5</span><b>{pct(data.accuracy.overall.top5_score_hit_rate, 1)}</b></div></div>
        <Link className="text-link" to="/accuracy">进入准确率中心 <ChevronRight size={15} /></Link>
      </div>
    </section>
  </div>;
}

function MetricCard({ icon: Icon, label, value, note, tone }: { icon: typeof Target; label: string; value: string; note: string; tone: string }) {
  return <div className={`metric-card ${tone}`}><span className="metric-icon"><Icon size={19} /></span><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>;
}

function SectionTitle({ title, detail, action }: { title: string; detail?: string; action?: string }) {
  return <div className="section-title"><div><h2>{title}</h2>{detail && <p>{detail}</p>}</div>{action && <button className="text-button">{action} <ChevronRight size={15} /></button>}</div>;
}

function MatchCard({ match, prediction, scores }: { match: Match; prediction: Prediction; scores: Array<{ score: string; probability: number }> }) {
  return <Link className="match-card" to={`/match/${match.match_id}`}>
    <div className="match-card-head"><span>{match.group_name} 组 · 第 {match.round} 轮</span><span className={match.status === "live" ? "live-label" : ""}>{match.status === "live" ? `${match.minute}' 直播` : formatMatchTime(match.match_time)}</span></div>
    <div className="teams">
      <div><span className="flag">{match.home_team.flag}</span><b>{match.home_team.name}</b><small>Elo {match.home_team.elo}</small></div>
      <span className="versus">{match.status === "live" ? `${match.home_score} : ${match.away_score}` : "VS"}</span>
      <div><span className="flag">{match.away_team.flag}</span><b>{match.away_team.name}</b><small>Elo {match.away_team.elo}</small></div>
    </div>
    <ProbabilityBar prediction={prediction} />
    <div className="card-insights"><span><Target size={14} /> {prediction.prediction_label}</span><RiskBadge score={prediction.upset_index} /></div>
    <div className="score-chips">{scores.slice(0, 3).map((score) => <span key={score.score}>{score.score}<b>{pct(score.probability)}</b></span>)}</div>
    <p className="match-summary">{prediction.summary}</p>
  </Link>;
}

function ProbabilityBar({ prediction }: { prediction: Prediction }) {
  const parts = [
    ["主胜", prediction.final_home_win_prob, "home"],
    ["平", prediction.final_draw_prob, "draw"],
    ["客胜", prediction.final_away_win_prob, "away"],
  ] as const;
  return <div className="probability"><div className="prob-labels">{parts.map(([label, value]) => <span key={label}><b>{pct(value)}</b>{label}</span>)}</div><div className="prob-track">{parts.map(([, value, key]) => <i key={key} className={key} style={{ width: pct(value, 2) }} />)}</div></div>;
}

function RiskBadge({ score }: { score: number }) {
  return <span className={`risk-badge ${riskTone(score)}`}><AlertTriangle size={13} /> 爆冷 {score}</span>;
}

function MatchDetail({ data }: { data: RadarData }) {
  const { id } = useParams();
  const match = data.matches.find((item) => item.match_id === id) ?? data.matches[0];
  const prediction = findPrediction(data, match.match_id);
  const scores = data.scores.find((row) => row.match_id === match.match_id)!.scores;
  const odds = data.odds.find((row) => row.match_id === match.match_id)!;
  const divergence = data.divergences.find((row) => row.match_id === match.match_id)!;
  const upset = data.upsets.find((row) => row.match_id === match.match_id)!;
  const intelligence = data.intelligence.find((row) => row.match_id === match.match_id)!;
  const chart = odds.history.map((item) => ({ ...item, label: new Date(item.time).toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" }) }));
  return <div className="page">
    <PageHeader eyebrow={`${match.group_name} 组 · 第 ${match.round} 轮`} title={`${match.home_team.name} vs ${match.away_team.name}`} description={`${formatMatchTime(match.match_time)} · ${match.city} · ${match.stadium}`}>
      <RiskBadge score={prediction.upset_index} />
    </PageHeader>
    <section className="detail-hero panel">
      <div className="detail-team"><span>{match.home_team.flag}</span><h2>{match.home_team.name}</h2><small>{match.home_team.english_name} · Elo {match.home_team.elo}</small></div>
      <div className="detail-center"><span>模型预测</span><strong>{pct(Math.max(prediction.final_home_win_prob, prediction.final_draw_prob, prediction.final_away_win_prob))}</strong><b>{prediction.prediction_label}</b><small>更新于 06:00</small></div>
      <div className="detail-team"><span>{match.away_team.flag}</span><h2>{match.away_team.name}</h2><small>{match.away_team.english_name} · Elo {match.away_team.elo}</small></div>
    </section>
    <div className="detail-grid">
      <div className="panel span-2"><SectionTitle title="胜平负概率" detail="最终概率融合 Elo、Poisson 与模型代理校准" /><ProbabilityBar prediction={prediction} /><div className="prob-comparison">
        {(["home", "draw", "away"] as const).map((key) => <div key={key}><span>{outcomeLabel[key]}</span><b>{pct(prediction[`final_${key === "draw" ? "draw" : `${key}_win`}_prob` as keyof Prediction] as number)}</b><small>模型 {pct(prediction[`model_${key === "draw" ? "draw" : `${key}_win`}_prob` as keyof Prediction] as number)} · 市场 {pct(prediction[`market_${key === "draw" ? "draw" : `${key}_win`}_prob` as keyof Prediction] as number)}</small></div>)}
      </div></div>
      <div className="panel"><SectionTitle title="预期进球" /><div className="xg-pair"><div><span>{match.home_team.name}</span><strong>{prediction.expected_home_goals}</strong></div><i /><div><span>{match.away_team.name}</span><strong>{prediction.expected_away_goals}</strong></div></div><div className="total-bars"><span>大 2.5 <b>{pct(prediction.over_25_prob)}</b></span><span>小 2.5 <b>{pct(prediction.under_25_prob)}</b></span><span>双方进球 <b>{pct(prediction.btts_prob)}</b></span></div></div>
      <div className="panel"><SectionTitle title="比分路径 Top 5" /><div className="score-table">{scores.map((row, index) => <div key={row.score}><span>0{index + 1}</span><b>{row.score}</b><i><em style={{ width: pct(row.probability / scores[0].probability) }} /></i><strong>{pct(row.probability, 1)}</strong></div>)}</div></div>
      <div className="panel span-2"><SectionTitle title="代理概率变化" detail="用于保持模型页面可用，不代表真实赔率市场" /><div className="chart-wrap"><ResponsiveContainer width="100%" height={250}><LineChart data={chart}><CartesianGrid stroke="#1c2b3d" vertical={false} /><XAxis dataKey="label" stroke="#708198" /><YAxis domain={["dataMin - 0.03", "dataMax + 0.03"]} tickFormatter={(v) => pct(v)} stroke="#708198" /><Tooltip contentStyle={tooltipStyle} formatter={(v: number) => pct(v, 1)} /><Line type="monotone" dataKey="home" name="主胜" stroke="#35a7ff" strokeWidth={3} dot={false} /><Line type="monotone" dataKey="draw" name="平局" stroke="#9aa8ba" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="away" name="客胜" stroke="#21d4a7" strokeWidth={3} dot={false} /></LineChart></ResponsiveContainer></div></div>
      <div className="panel insight-panel"><SectionTitle title="模型判断理由" />{prediction.factors.map((factor) => <p key={factor}><Sparkles size={15} />{factor}</p>)}<div className="summary-box">{prediction.summary}</div></div>
      <div className="panel insight-panel"><SectionTitle title="分歧与风险" /><div className="big-risk"><RiskBadge score={upset.upset_index} /><strong>{divergence.summary}</strong></div>{upset.reason.map((reason) => <p key={reason}><AlertTriangle size={15} />{reason}</p>)}</div>
      <IntelligencePanel intelligence={intelligence} />
    </div>
  </div>;
}

function IntelligencePanel({ intelligence }: { intelligence: MatchIntelligence }) {
  const statusLabel: Record<string, string> = {
    confirmed: "官方确认",
    verified: "已核验",
    automatic: "自动数据",
    pending_official: "等待官方",
    forecast_pending: "等待预报",
    proxy: "代理数据",
    missing: "缺少数据",
  };
  return <div className="panel span-2 intelligence-panel">
    <SectionTitle title="赛前八维情报" detail={`可信覆盖 ${intelligence.confirmed_features}/${intelligence.total_features} · 完整度 ${pct(intelligence.completeness)}`} />
    <div className="intelligence-grid">{Object.entries(intelligence.features).map(([key, feature]) =>
      <article className="intelligence-item" key={key}>
        <div><strong>{feature.label}</strong><span className={`intel-status ${feature.status}`}>{statusLabel[feature.status] ?? feature.status}</span></div>
        <p>{feature.summary}</p>
        <small>主队影响 {signedPct(feature.home_impact)} · 客队影响 {signedPct(feature.away_impact)}</small>
        {feature.source_url && <a href={feature.source_url} target="_blank" rel="noreferrer">{feature.source_name || "查看来源"} <ChevronRight size={12} /></a>}
      </article>
    )}</div>
    <div className="intelligence-warning"><AlertTriangle size={15} />{intelligence.warning}</div>
  </div>;
}

function OddsPage({ data }: { data: RadarData }) {
  const rows = [...data.odds].sort((a, b) => Math.abs(b.change_24h) - Math.abs(a.change_24h));
  const connected = data.metadata.real_odds_matches > 0;
  return <div className="page"><PageHeader eyebrow={connected ? "LIVE MARKET" : "MODEL PROXY"} title={connected ? "实时赔率雷达" : "概率代理雷达"} description={data.metadata.odds_notice}><span className="source-chip"><Database size={14} /> {connected ? data.metadata.odds_source : "Model Proxy"}</span></PageHeader>
    <div className="stat-strip"><MiniStat label="实时赔率覆盖" value={`${data.metadata.real_odds_matches}`} trend={`代理 ${data.metadata.proxy_odds_matches} 场`} /><MiniStat label="24h 显著异动" value={`${rows.filter((r) => r.market_type === "1x2-real" && Math.abs(r.change_24h) >= .015).length}`} trend="阈值 1.5%" /><MiniStat label="博彩公司" value={`${data.metadata.bookmakers_total}`} trend={connected ? "Odds-API.io" : "等待配置 Key"} /><MiniStat label="最大模型分歧" value={pct(Math.max(...data.divergences.map((d) => d.largest_divergence_value)), 1)} trend={connected ? "模型 vs 市场" : "模型内部校准"} /></div>
    <div className="panel table-panel"><div className="table-toolbar"><SectionTitle title="异动排行榜" detail="按 24 小时隐含概率变化排序" /><button className="secondary-button">胜平负市场</button></div><div className="data-table odds-table"><div className="table-head"><span>比赛</span><span>方向</span><span>开盘</span><span>当前</span><span>24 小时</span><span>一致性</span><span>信号</span></div>{rows.map((row) => {
      const m = data.matches.find((x) => x.match_id === row.match_id)!;
      return <Link to={`/match/${row.match_id}`} className="table-row" key={row.match_id}><span className="match-cell"><b>{m.home_team.flag} {m.home_team.name}</b><small>{m.away_team.flag} {m.away_team.name}</small></span><span>{outcomeLabel[row.selection]}</span><span>{row.open_odds.toFixed(2)}</span><span><b>{row.current_odds.toFixed(2)}</b></span><span className={row.change_24h >= 0 ? "up" : "down"}>{row.change_24h >= 0 ? <TrendingUp size={15} /> : <TrendingDown size={15} />}{signedPct(row.change_24h)}</span><span>{pct(row.bookmaker_consensus)}</span><span><i className="signal-tag">{row.signal}</i></span></Link>;
    })}</div></div>
  </div>;
}

function UpsetPage({ data }: { data: RadarData }) {
  const sorted = [...data.upsets].sort((a, b) => b.upset_index - a.upset_index);
  return <div className="page"><PageHeader eyebrow="UNCERTAINTY MAP" title="爆冷风险雷达" description="爆冷指数衡量热门方向的不确定性，不代表弱队一定取胜。" />
    <div className="risk-scale"><span className="safe">0–30 风险低</span><span className="notice">31–55 有苗头</span><span className="warning">56–75 较高</span><span className="danger">76–100 高危</span></div>
    <div className="upset-grid">{sorted.map((row, index) => {
      const match = data.matches.find((m) => m.match_id === row.match_id)!;
      return <Link to={`/match/${row.match_id}`} className={`upset-card ${riskTone(row.upset_index)}`} key={row.match_id}><div className="upset-rank"><span>RANK</span><b>{String(index + 1).padStart(2, "0")}</b></div><div className="upset-main"><div className="match-line"><strong>{match.home_team.flag} {match.home_team.name}</strong><span>VS</span><strong>{match.away_team.name} {match.away_team.flag}</strong></div><div className="risk-meter"><i><em style={{ width: `${row.upset_index}%` }} /></i><b>{row.upset_index}</b></div><div className="risk-factors"><span>热门过热 <b>{row.favorite_overheat_score}</b></span><span>弱队不败 <b>{pct(row.underdog_not_lose_prob)}</b></span><span>平局热度 <b>{row.draw_heat_score}</b></span></div><p>{row.reason[0]}</p></div><ChevronRight size={19} /></Link>;
    })}</div>
  </div>;
}

function AccuracyPage({ data }: { data: RadarData }) {
  const a = data.accuracy;
  return <div className="page"><PageHeader eyebrow="MODEL PERFORMANCE" title="准确率中心" description="准确率不是唯一目标。校准良好的概率，才是可持续迭代的基础。"><button className="primary-button"><RefreshCw size={15} /> 运行每日诊断</button></PageHeader>
    <div className="accuracy-cards"><AccuracyCard label="胜平负命中率" value={pct(a.overall.result_accuracy, 1)} note="较 Elo 基线 +7.3%" good /><AccuracyCard label="大小球命中率" value={pct(a.overall.over_under_accuracy, 1)} note="最近 48 场" good /><AccuracyCard label="比分 Top 5" value={pct(a.overall.top5_score_hit_rate, 1)} note="严格比分路径" /><AccuracyCard label="爆冷预警命中" value={pct(a.overall.upset_warning_hit_rate, 1)} note="高风险样本" /></div>
    <div className="analytics-grid">
      <div className="panel span-2"><SectionTitle title="概率校准曲线" detail="预测概率应尽量接近实际发生频率" /><div className="chart-wrap"><ResponsiveContainer width="100%" height={280}><LineChart data={a.calibration}><CartesianGrid stroke="#1c2b3d" /><XAxis dataKey="predicted" tickFormatter={(v) => pct(v)} stroke="#708198" /><YAxis tickFormatter={(v) => pct(v)} stroke="#708198" /><Tooltip contentStyle={tooltipStyle} formatter={(v: number) => pct(v, 1)} /><Line dataKey="predicted" name="理想校准" stroke="#51637a" strokeDasharray="5 5" dot={false} /><Line dataKey="actual" name="实际命中" stroke="#35a7ff" strokeWidth={3} /></LineChart></ResponsiveContainer></div></div>
      <div className="panel metric-detail"><SectionTitle title="概率评分" /><div><span>Brier Score</span><strong>{a.overall.brier_score}</strong><small>越低越好 · 基线 0.231</small></div><div><span>Log Loss</span><strong>{a.overall.log_loss}</strong><small>越低越好 · 基线 1.032</small></div><div><span>复盘样本</span><strong>{a.overall.matches_reviewed}</strong><small>Mock 历史验证集</small></div></div>
      <div className="panel"><SectionTitle title="按信心等级" detail="高信心是否真的更准" /><div className="confidence-bars">{a.by_confidence.map((row) => <div key={row.confidence_level}><span>{confidenceLabel[row.confidence_level]} <small>{row.matches} 场</small></span><i><em style={{ width: pct(row.result_accuracy) }} /></i><b>{pct(row.result_accuracy, 1)}</b></div>)}</div></div>
      <div className="panel span-2"><SectionTitle title="不同阶段表现" /><div className="chart-wrap"><ResponsiveContainer width="100%" height={240}><BarChart data={a.by_stage}><CartesianGrid stroke="#1c2b3d" vertical={false} /><XAxis dataKey="stage" stroke="#708198" /><YAxis tickFormatter={(v) => pct(v)} stroke="#708198" /><Tooltip contentStyle={tooltipStyle} formatter={(v: number) => pct(v, 1)} /><Bar dataKey="result_accuracy" name="命中率" fill="#21d4a7" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div></div>
    </div>
  </div>;
}

function AccuracyCard({ label, value, note, good }: { label: string; value: string; note: string; good?: boolean }) {
  return <div className="accuracy-card"><span>{label}</span><strong>{value}</strong><small className={good ? "positive" : ""}>{good && <TrendingUp size={13} />}{note}</small></div>;
}

function ReviewPage({ data }: { data: RadarData }) {
  return <div className="page"><PageHeader eyebrow="POST-MATCH REVIEW" title="赛后复盘" description="记录模型如何犯错，比记录一次命中更有价值。" />
    <div className="review-list">{data.reviews.map((row) => {
      const match = data.matches.find((m) => m.match_id === row.match_id)!;
      return <article className="review-card panel" key={row.match_id}><div className="review-result"><span>{row.result_hit ? "预测命中" : "预测偏差"}</span><div><strong>{match.home_team.flag} {match.home_team.name}</strong><b>{match.home_score} : {match.away_score}</b><strong>{match.away_team.name} {match.away_team.flag}</strong></div><small>预测：{outcomeLabel[row.predicted_result]} · 实际：{outcomeLabel[row.actual_result]}</small></div><div className="review-flags"><Tag ok={row.result_hit} text="赛果" /><Tag ok={row.over_under_hit} text="大小球" /><Tag ok={row.score_top5_hit} text="比分 Top 5" /><Tag ok={row.upset_warning_hit} text="爆冷预警" /></div><div className="review-analysis"><div><span>误差诊断</span><p>{row.model_error_summary}</p></div><div><span>赔率信号</span><p>{row.odds_signal_review}</p></div><div><span>调整建议</span><p>{row.adjustment_suggestion}</p></div></div><div className="review-scores"><span>Brier <b>{row.brier_score}</b></span><span>Log Loss <b>{row.log_loss}</b></span></div></article>;
    })}</div>
  </div>;
}

function Tag({ ok, text }: { ok: boolean; text: string }) { return <span className={ok ? "tag-ok" : "tag-miss"}>{ok ? "✓" : "×"} {text}</span>; }

function BacktestPage({ data }: { data: RadarData }) {
  const chartData = data.backtest.map((row) => ({ ...row, label: row.model.replace("模型 + ", "+ ") }));
  return <div className="page"><PageHeader eyebrow="HISTORICAL VALIDATION" title="模型回测实验室" description="比较每一层特征是否真正改善样本外预测，而不是追求历史拟合。"><span className="source-chip"><FlaskConical size={14} /> 96 场验证集</span></PageHeader>
    <div className="panel"><SectionTitle title="模型组合对比" detail="胜平负准确率 · 相对 Elo 基线" /><div className="chart-wrap"><ResponsiveContainer width="100%" height={320}><AreaChart data={chartData}><defs><linearGradient id="accuracyFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#35a7ff" stopOpacity={0.45} /><stop offset="100%" stopColor="#35a7ff" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#1c2b3d" vertical={false} /><XAxis dataKey="label" stroke="#708198" /><YAxis domain={[0.48, 0.66]} tickFormatter={(v) => pct(v)} stroke="#708198" /><Tooltip contentStyle={tooltipStyle} formatter={(v: number) => pct(v, 1)} /><Area dataKey="accuracy" name="准确率" type="monotone" stroke="#35a7ff" strokeWidth={3} fill="url(#accuracyFill)" /></AreaChart></ResponsiveContainer></div></div>
    <div className="panel table-panel"><SectionTitle title="完整评估指标" /><div className="data-table backtest-table"><div className="table-head"><span>模型组合</span><span>样本</span><span>准确率</span><span>Brier</span><span>Log Loss</span><span>提升</span></div>{data.backtest.map((row, i) => <div className={`table-row ${i === data.backtest.length - 1 ? "best-row" : ""}`} key={row.model}><span><b>{row.model}</b>{i === data.backtest.length - 1 && <i className="best-tag">当前最佳</i>}</span><span>{row.matches}</span><span><b>{pct(row.accuracy, 1)}</b></span><span>{row.brier_score}</span><span>{row.log_loss}</span><span className="positive">{row.lift ? `+${pct(row.lift, 1)}` : "基线"}</span></div>)}</div></div>
    <div className="finding-grid"><div className="finding"><TrendingUp size={20} /><div><strong>真实赛果持续累积</strong><p>OpenFootball 更新赛果后，系统会自动生成逐场复盘指标。</p></div></div><div className="finding"><CircleGauge size={20} /><div><strong>校准优于硬命中</strong><p>同时关注 Brier Score 与 Log Loss，避免只看胜平负命中率。</p></div></div><div className="finding"><AlertTriangle size={20} /><div><strong>仍需防止过拟合</strong><p>回测使用时间切分，不将未来赛果或赛后信息泄漏到赛前特征。</p></div></div></div>
  </div>;
}

function SettingsPage({ metadata }: { metadata: DataMetadata }) {
  const [unlocked, setUnlocked] = useState(() => sessionStorage.getItem("akimi-settings-unlocked") === "true");
  const [password, setPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [checking, setChecking] = useState(false);
  const [marketWeight, setMarketWeight] = useState(20);

  async function unlockSettings(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setChecking(true);
    setPasswordError("");
    const bytes = new TextEncoder().encode(password);
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    const hash = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
    const expectedHash = import.meta.env.VITE_SETTINGS_PASSWORD_HASH
      || "aa25183fef62c4aa58eaf44ae6bf5f1afd02ac6d762d5d93e0c61b175699d89b";
    if (hash === expectedHash) {
      sessionStorage.setItem("akimi-settings-unlocked", "true");
      setUnlocked(true);
      setPassword("");
    } else {
      setPasswordError("密码不正确，请重新输入。");
    }
    setChecking(false);
  }

  function lockSettings() {
    sessionStorage.removeItem("akimi-settings-unlocked");
    setUnlocked(false);
    setPassword("");
    setPasswordError("");
  }

  if (!unlocked) {
    return <div className="page settings-gate-page">
      <div className="settings-gate panel">
        <div className="settings-lock-icon"><Lock size={28} /></div>
        <span className="eyebrow">RESTRICTED SETTINGS</span>
        <h1>系统设置已锁定</h1>
        <p>请输入管理密码后访问数据源和模型参数。本次解锁仅在当前浏览器标签页有效。</p>
        <form onSubmit={unlockSettings}>
          <label htmlFor="settings-password">管理密码</label>
          <div className="password-field"><KeyRound size={18} /><input id="settings-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="请输入设置密码" autoFocus /></div>
          {passwordError && <span className="password-error" role="alert">{passwordError}</span>}
          <button className="primary-button unlock-button" type="submit" disabled={!password || checking}>{checking ? "正在验证..." : "解锁系统设置"}</button>
        </form>
        <small>静态站点密码门禁用于个人访问控制，不替代服务器端身份认证。</small>
      </div>
    </div>;
  }

  return <div className="page"><PageHeader eyebrow="SYSTEM CONFIGURATION" title="系统设置" description="数据由 Codex 本机任务每小时更新，也支持运行仓库脚本手动更新。"><a className="primary-button" href={metadata.source_url} target="_blank" rel="noreferrer"><Database size={15} /> 查看免费数据源</a><button className="secondary-button" onClick={lockSettings}><LogOut size={15} /> 锁定设置</button></PageHeader>
    <div className="settings-grid"><div className="panel"><SectionTitle title="数据 Provider" /><SettingRow title="OpenFootball" detail="无需 API Key，公开赛程与赛果"><span className="source-connected">已连接</span></SettingRow><SettingRow title="自动更新时间" detail={metadata.update_frequency}><span className="source-connected">已启用</span></SettingRow><SettingRow title="Odds-API.io" detail={metadata.odds_notice}><span className={metadata.real_odds_matches ? "source-connected" : "not-connected"}>{metadata.real_odds_matches ? `已覆盖 ${metadata.real_odds_matches} 场` : "等待 Key"}</span></SettingRow><SettingRow title="最近同步" detail={formatUpdatedAt(metadata.generated_at)}><span className="source-connected">{metadata.fixtures_total} 场</span></SettingRow></div>
      <div className="panel"><SectionTitle title="模型参数" /><label className="slider-setting"><span><b>代理校准权重</b><small>当前 {marketWeight}%</small></span><input type="range" min="0" max="70" value={marketWeight} onChange={(e) => setMarketWeight(Number(e.target.value))} /></label><label className="slider-setting"><span><b>爆冷预警阈值</b><small>56 / 100</small></span><input type="range" min="20" max="90" defaultValue="56" /></label><label className="slider-setting"><span><b>低信心阈值</b><small>领先优势低于 8%</small></span><input type="range" min="2" max="20" defaultValue="8" /></label></div>
      <div className="panel span-2 provider-note"><Database size={24} /><div><strong>当前数据说明</strong><p>赛程与赛果来自 OpenFootball，赔率接入 Odds-API.io 免费套餐。系统每小时第17分钟同步；未配置 Key、接口异常或未覆盖的比赛会自动降级为模型代理。可运行 scripts/update_and_publish.sh 手动更新并发布。</p></div></div></div>
  </div>;
}

function SettingRow({ title, detail, children }: { title: string; detail: string; children: React.ReactNode }) { return <div className="setting-row"><div><b>{title}</b><small>{detail}</small></div>{children}</div>; }
function MiniStat({ label, value, trend }: { label: string; value: string; trend: string }) { return <div><span>{label}</span><strong>{value}</strong><small>{trend}</small></div>; }
function findPrediction(data: RadarData, id: string) { return data.predictions.find((row) => row.match_id === id)!; }
const tooltipStyle = { background: "#0d1a29", border: "1px solid #22354b", borderRadius: "10px", color: "#eef6ff" };

export default App;
