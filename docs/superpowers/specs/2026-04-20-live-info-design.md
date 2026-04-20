# 演唱会信息分发系统 — 设计文档

日期：2026-04-20
作者：brainstorming session

## 背景与目标

为项目内组员提供按艺人订阅的演唱会信息自动分发。每日通过 GitHub Actions 抓取固定数据源（首期猫眼演出）并用 LLM 联网搜索交叉验证，把新增演出或状态变化推送到用户配置的通知渠道（飞书 webhook + 邮件）。

## 范围

**In scope（MVP）**
- 数据源：猫眼演出（通过 `m.dianping.com/myshow` AJAX 接口）
- LLM 验证：OpenAI 兼容网关（带 web search 能力）
- 存储：Supabase
- 订阅维度：艺人（含别名）
- 通知渠道：飞书群 webhook、邮件
- 运行频率：每日一次
- 状态变化通知：verified 状态、开票状态、开票时间变化

**Out of scope（首期不做）**
- 城市/价格/日期范围过滤
- 网页配置前端（用户订阅直接改 Supabase 表或后续加一个 Pages 表单）
- 多数据源（大麦、纷玩岛等）
- 港澳台/海外站点

## 总体架构

单 GitHub Actions workflow、单 Python 脚本串行执行：

```
cron(daily) → crawler(猫眼) → llm_verifier → alias_resolver
           → cross_validate → diff_vs_snapshot → dispatcher(飞书/邮件)
                          ↕
                       Supabase
```

技术栈：Python 3.11 · httpx · pydantic · supabase-py。

## 数据模型（Supabase）

```sql
artists (
  id uuid pk,
  canonical_name text unique,
  created_at timestamptz
);

artist_aliases (
  alias text pk,
  artist_id uuid fk -> artists.id,
  source text            -- 'manual' | 'llm'
);

concerts (
  id uuid pk,
  artist_id uuid fk,
  city text,
  show_date date,
  venue text,
  status text,           -- 'unverified' | 'verified'
  sale_status text,      -- 'announced' | 'on_sale' | 'sold_out' | 'unknown'
  sale_open_at timestamptz null,
  source_url text null,         -- 猫眼演出详情页
  source_performance_id text null,  -- 猫眼 performanceId
  llm_sources jsonb null,
  first_seen_at timestamptz,
  last_seen_at timestamptz,
  unique (artist_id, city, show_date)
);

concert_snapshots (
  id bigserial pk,
  concert_id uuid fk,
  status text,
  sale_status text,
  sale_open_at timestamptz null,
  snapshot_at timestamptz
);

users (
  id uuid pk,
  name text,
  email text null,
  feishu_webhook text null,
  notify_on_status_change bool default true
);

subscriptions (
  user_id uuid fk,
  artist_id uuid fk,
  primary key (user_id, artist_id)
);
```

演唱会唯一键：`(artist_id, city, show_date)`。

## 核心流程

1. **加载订阅**：从 `subscriptions` 聚合本轮关注的艺人集合（canonical 去重）。
2. **Crawler（猫眼）**：对每个艺人调用猫眼演出搜索 AJAX 接口：
   - 搜索：`GET https://m.dianping.com/myshow/ajax/performances/1;st=0;k={keyword};p=1;s=20;tft=0?cityId=0`（`cityId=0` 全国）
   - 详情：`GET https://m.dianping.com/myshow/ajax/performance/{performanceId};poi=false`（取 `priceRange` / `sellPriceRange` / `ticketStatus`）
   - Headers：`User-Agent: Mozilla/5.0 ...`、`Referer: https://show.maoyan.com/`
   - 提取字段：`performanceId`、`name`、`shopName`(venue)、`showTimeRange`、`cityName`、`ticketStatus`
   - `ticketStatus` 映射到统一 `sale_status`（`announced` / `on_sale` / `sold_out` / `unknown`）
   - 单艺人失败隔离，最多重试 2 次（指数退避）
3. **LLM Verifier**：调用 OpenAI 兼容网关并启用 web_search 工具，固定 prompt 要求返回结构化 JSON：`[{artist, city, date, venue, sources:[urls]}]`。
4. **别名归一化**：所有外部艺人名先查 `artist_aliases`；未命中时让 LLM 判一次归属，写回表，后续命中走缓存。
5. **交叉验证**：按 `(artist_id, city, date)` 合并两路：
   - 两路都有 → `status = verified`
   - 只猫眼 → `status = unverified`
   - 只 LLM → `status = unverified`
6. **Diff 快照**：与 `concerts` 现有记录对比产生事件：
   - `new`：新出现的演出
   - `status_change`：`status / sale_status / sale_open_at` 变化
   写 `concert_snapshots`，更新 `concerts`。
7. **通知分发**：对每个事件查订阅该艺人的用户，按 `users` 偏好渲染并发送。失败记日志不阻塞其他。同一用户本轮多条事件合并成一条消息。

## 通知设计

**渠道抽象**
```python
class Notifier(Protocol):
    def send(self, user: User, events: list[Event]) -> Result: ...
```
- `EmailNotifier`：SMTP（配置在 Secrets）
- `FeishuNotifier`：POST `user.feishu_webhook`

分发器按非空字段决定走哪一路（都配就都发）。

**消息模板**
```
【新演唱会】Taylor Swift · 上海 · 2026-08-12
场馆：梅赛德斯奔驰文化中心
状态：✅ 已验证（猫眼 + LLM）
售票：未开票 · 开票时间待定
链接：https://show.maoyan.com/...
```
```
【状态变化】Taylor Swift · 上海 · 2026-08-12
售票状态：未开票 → 已开票（2026-05-01 10:00）
```

去重由 `concert_snapshots` diff 保证，已通知事件不重复推送。

## 配置与密钥

GitHub Secrets：
- `SUPABASE_URL` / `SUPABASE_SERVICE_KEY`
- `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM`

Workflow：`cron: "0 1 * * *"`（UTC 01:00 ≈ 北京 09:00），支持 `workflow_dispatch` 手动触发 + `--dry-run` 开关（不发通知、不写库）。

## 错误处理

- 外部调用全部 timeout + 指数退避重试
- LLM 返回非合法 JSON 时重试一次带修正 prompt，仍失败则跳过该艺人的 LLM 路径（仍可走单源事件）
- 单艺人/单用户失败隔离，聚合到 run summary
- 失败率超过 30% 时 workflow 以非零退出码收尾，触发 Actions 告警

## 测试策略

- **单元测试**：猫眼 AJAX 响应解析（JSON fixture）、ticketStatus 映射、diff 逻辑、别名归一化、消息渲染
- **集成测试**（可选 live 开关）：Supabase test schema + mock LLM
- **CI**：PR 触发 lint + 单元测试

## 可观测性

每次 run 往 `$GITHUB_STEP_SUMMARY` 写一份 Markdown：抓取条数、验证条数、新增事件、通知投递统计、失败艺人列表。

## 仓库结构

```
live_info/
  __init__.py
  run.py                  # 入口
  config.py
  crawlers/maoyan.py
  llm/verifier.py
  llm/alias_resolver.py
  db/supabase_client.py
  diff.py
  notifiers/email.py
  notifiers/feishu.py
  notifiers/dispatcher.py
  models.py               # pydantic
tests/
.github/workflows/daily.yml
pyproject.toml
README.md
```

## 关键决策

| 决策 | 选择 | 备选 |
|---|---|---|
| 编排 | 单 workflow 单 job 串行 | 多 job 流水线 / Supabase Edge Functions |
| 订阅维度 | 仅艺人（含别名） | 加城市/日期/价格 |
| 唯一键 | (artist, city, date) | 大麦 performance id / LLM hash |
| 别名存储 | Supabase `artist_aliases` | 仓库 yml / LLM 每次动态判 |
| 首期数据源 | 猫眼（m.dianping.com AJAX） | 大麦 / 多源并行。参考实现：https://github.com/kingqiu/concert-monitor-skill/blob/main/scripts/monitor.py |
| 首期通道 | 飞书 + 邮件 | Telegram / 企微 / 钉钉 |
