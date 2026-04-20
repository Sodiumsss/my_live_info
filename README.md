# live_info

演唱会信息自动分发。每日通过 GitHub Actions 抓取猫眼 + LLM 联网交叉验证，推送到用户订阅的飞书 webhook / 邮箱。

详见 [设计文档](docs/superpowers/specs/2026-04-20-live-info-design.md) 与 [实施计划](docs/superpowers/plans/2026-04-20-live-info.md)。

## 首次部署

1. 在 Supabase 创建项目，SQL Editor 执行 `db/schema.sql`
2. 在 `users` / `artists` / `subscriptions` 表中插入组员与订阅
3. 在 GitHub Repo → Settings → Secrets 配置：
   - `SUPABASE_URL`、`SUPABASE_SERVICE_KEY`
   - `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`
   - `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM`
4. 在 Actions 页手动 `workflow_dispatch` 跑一次（可勾 dry-run）

## 本地开发

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

## 订阅管理（MVP）

直接在 Supabase Table Editor 里增删 `users` / `subscriptions`；`artist_aliases` 可手动录入偏好别名（`source='manual'`）。
