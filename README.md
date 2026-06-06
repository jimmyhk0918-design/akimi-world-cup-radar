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
- 无 API Key 的 Mock 数据完整闭环

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

前端通过 `public/data/*.json` 读取数据。`npm run generate:data` 会用固定随机种子重新生成稳定的 Mock 数据。

## 目录结构

```text
src/                  React 页面、组件和数据类型
public/data/          前端读取的静态 JSON
scripts/models/       Elo、Poisson、去水、融合和评分函数
scripts/providers/    免费数据源 Provider 骨架
scripts/generate_data.py
tests/                Python 模型测试
.github/workflows/    Pages 部署与数据更新
```

## 数据源策略

系统采用可替换 Provider，不让前端直接访问第三方 API：

1. API-Football：赛程、比分、阵容与比赛事件主数据源。
2. football-data.org：赛程和赛果备用源。
3. OpenFootball：无 Key 冷启动及静态赛程降级源。
4. 独立赔率 Provider：拉取胜平负、大小球和让球，并由 Actions 保存历史快照。

当前 `generate_data.py` 默认使用 Mock 数据。Provider 类已经提供接入边界，正式切换时应先把第三方结构转换为项目内部 JSON 契约，再交给模型计算。

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
USE_MOCK_DATA=true
```

没有 Key 时保持 `true`，系统仍可构建和完整展示。

## GitHub Pages 部署

1. 创建仓库 `akimi-world-cup-radar`。
2. 推送代码到 `main`。
3. 在 **Settings → Pages → Build and deployment** 中选择 **GitHub Actions**。
4. 手动运行 `Deploy GitHub Pages`，或等待 push 自动触发。

应用使用 Hash Router 和相对资源路径，因此可以直接部署在仓库子路径，不需要额外配置 404 回退。

## 数据更新 Workflow

`update-data.yml` 每小时第 17 分钟运行一次，也支持手动触发。它会：

1. 生成或拉取数据。
2. 执行模型测试。
3. 只在 JSON 变化时提交。
4. 触发 Pages 重新部署。

免费 API 有请求额度限制，因此 MVP 不采用 5 分钟轮询。未来可根据比赛时间动态调整调用频率，并对接口结果做本地缓存。

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
