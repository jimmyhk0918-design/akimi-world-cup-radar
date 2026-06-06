# 阿基米世界杯雷达

2026 世界杯赛事结果预测与模型校准系统。项目通过球队强度、Poisson 比分分布、去水市场概率、模型分歧和赛后回测，持续评估并改善预测概率。

> 本项目只用于个人赛事研究，不提供投注策略、资金管理、投注记录或自动下注功能。

## 当前功能

- 今日赛事雷达与比赛详情
- 胜平负、比分 Top 5、大小球和双方进球概率
- 赔率变化、去水市场概率和模型市场分歧
- 爆冷风险指数与低信心表达
- 准确率中心：命中率、Brier Score、Log Loss、校准曲线
- 单场赛后复盘和模型调整建议
- 多模型组合历史回测
- 移动端适配
- 系统设置密码门禁与会话锁定
- 无 API Key 的 OpenFootball 真实赛程与赛果
- 每小时自动更新和一键手动更新脚本

## 技术栈

- React 18、TypeScript、Vite
- Recharts、Lucide Icons、原生响应式 CSS
- Python 3.9+ 标准库模型与数据生成脚本
- GitHub Actions、GitHub Pages、静态 JSON

## 本地运行

```bash
npm install
npm run generate:data
npm run dev
```

生产构建：

```bash
npm run test:model
npm run build
npm run preview
```

前端通过 `public/data/*.json` 读取数据。`npm run generate:data` 默认从 OpenFootball
公开 JSON 拉取 2026 世界杯赛程和赛果，再重新计算预测、比分概率、爆冷指数与复盘指标。

## 目录结构

```text
src/                  React 页面、组件和数据类型
public/data/          前端读取的静态 JSON
scripts/models/       Elo、Poisson、去水、融合和评分函数
scripts/providers/    免费数据源 Provider 骨架
scripts/generate_data.py
tests/                Python 模型测试
workflow-templates/   Pages 部署与数据更新模板
```

## 数据源策略

系统采用可替换 Provider，不让前端直接访问第三方 API：

1. OpenFootball：默认数据源，无需 API Key，提供公开赛程与赛果。
2. API-Football：已保留 Provider，可在取得免费 Key 后补充阵容、事件和更及时的比赛状态。
3. football-data.org：已保留 Provider，可作为带 Key 的备用赛程源。

OpenFootball 更新频率由社区数据维护决定，不是秒级直播接口。系统每小时检查一次：
源数据拉取或解析失败时任务会失败，并保留上一批有效 JSON，不会用空数据覆盖线上页面。

实时赔率使用 Odds-API.io。免费账号仍需 API Key；Key 仅由本机更新脚本或服务器端
任务读取，不进入前端构建。接口未配置、暂时失败或未覆盖某场时，该场自动降级为
`model_proxy`，页面会明确标识，不冒充博彩公司报价。

配置实时赔率：

1. 在 [Odds-API.io](https://odds-api.io) 注册免费账号并取得 API Key。
2. 在项目根目录创建 `.env`：

```text
ODDS_API_KEY=你的Key
ODDS_BOOKMAKERS=Bet365,Unibet,Betfair,Pinnacle
```

3. 运行 `bash scripts/update_and_publish.sh`。

系统会按比赛双方名称匹配事件，使用批量赔率接口获取多家公司胜平负赔率，执行去水、
平均概率、模型融合并保存每小时历史快照。批量接口每次最多处理 10 场，以减少额度消耗。

## 环境变量与 Secrets

复制 `.env.example` 可查看变量名称。密钥不得以 `VITE_` 开头，也不得写入 `public/data`。

在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中配置：

```text
API_FOOTBALL_KEY
FOOTBALL_DATA_KEY
ODDS_API_KEY
```

仓库变量：

```text
RADAR_DATA_SOURCE=openfootball
```

赛程数据源不需要 Key。`ODDS_API_KEY` 用于 Odds-API.io 实时赔率；不得以 `VITE_`
开头，也不得提交到仓库。

## 系统设置密码

系统设置页默认密码：

```text
akimi2026
```

验证成功后只在当前浏览器标签页保持解锁，关闭标签页或点击“锁定设置”后需要重新输入。

修改密码时，先生成新密码的 SHA-256：

```bash
node -e "require('crypto').webcrypto.subtle.digest('SHA-256',new TextEncoder().encode('你的新密码')).then(x=>console.log(Buffer.from(x).toString('hex')))"
```

然后把输出值配置为构建环境变量：

```text
VITE_SETTINGS_PASSWORD_HASH=生成的SHA-256
```

这是静态站点的个人访问屏障，摘要仍会包含在前端构建中，不能替代服务器端登录和权限系统。

## GitHub Pages 部署

1. 创建仓库 `akimi-world-cup-radar`。
2. 推送代码到 `main`。
3. 在 **Settings → Pages → Build and deployment** 中选择从 `gh-pages` 分支发布。
4. 本机自动任务或手动脚本会构建并更新该分支。

应用使用 Hash Router 和相对资源路径，因此可以直接部署在仓库子路径，不需要额外配置 404 回退。

## 数据自动更新

当前已在 Codex 中启用本机自动任务，每小时第 17 分钟运行一次。它会：

1. 从 OpenFootball 拉取公开赛程与赛果。
2. 执行模型测试。
3. 重新计算预测数据并提交变化。
4. 构建站点并更新 `gh-pages`。

手动更新方法：

```bash
bash scripts/update_and_publish.sh
```

脚本会拉取数据、运行测试、构建页面、提交变化，并更新 `main` 与 `gh-pages`。
`workflow-templates/update-and-deploy.yml` 保留了 GitHub Actions 云端方案；当前 GitHub
令牌缺少 `workflow` 范围，因此尚未安装到 `.github/workflows/`。

## 预测模型

- **Elo**：描述球队长期相对强度，并加入轻量主场项。
- **Poisson**：根据双方预期进球生成比分矩阵。
- **赔率去水**：归一化隐含概率，移除理论返还率影响。
- **概率融合**：当前 Mock 模型使用 65% 基础模型和 35% 市场概率。
- **爆冷指数**：衡量热门方不确定性，不表示弱队必胜。

淘汰赛的胜平负口径固定为 90 分钟；晋级概率应作为独立市场和独立模型输出。

## 准确率评估

除胜平负命中率外，系统同时评估：

- 大小球命中率
- 比分 Top 5 命中率
- 爆冷预警命中率
- Brier Score
- Log Loss
- 概率校准曲线
- 不同阶段和信心等级表现

回测必须使用时间切分，禁止把未来赛果、收盘后信息或赛后统计泄漏到赛前特征中。

## 风险免责声明

本系统仅用于个人赛事数据分析、预测研究和模型复盘，不构成任何投注、购彩或投资建议。体育比赛结果具有高度不确定性，请理性看待模型结论。
