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

或使用下面的 Web 管理台。

## Web 管理台（GitHub Pages）

`web/` 是一个纯静态单页应用，部署到 GitHub Pages，用于快速增删改 `artists` / `users` / `subscriptions`，以及只读浏览 `concerts`。

### 安全模型

站点是公开的，但 `SUPABASE_SERVICE_KEY` **不会** 以明文出现在构建产物中：构建期用 `ADMIN_KEY`（一个强密码）做 PBKDF2-SHA256（60 万次迭代）+ AES-GCM 加密 service key，只把密文打包进 `config.js`。访客输入正确的 `ADMIN_KEY` 才能在浏览器里 WebCrypto 解密并操作 Supabase。

⚠️ `ADMIN_KEY` 必须强（推荐 ≥20 字符随机 / 4 词 diceware）。弱密码离线可暴破。

### 启用步骤

1. **Repository Secret** 新增 `ADMIN_KEY`（Settings → Secrets and variables → Actions → New repository secret）
   - 若 `ADMIN_KEY`、`SUPABASE_URL`、`SUPABASE_SERVICE_KEY` 任一未设置，`pages` workflow 会 **exit 1** 红灯失败
2. **Settings → Pages → Build and deployment → Source** 改为 **GitHub Actions**
3. 推送任何改动到 `web/`、`scripts/build_web_config.py` 或 `.github/workflows/pages.yml`，或在 Actions 页手动触发 `pages` workflow
4. 部署完成后访问 `https://<username>.github.io/<repo>/`，输入 `ADMIN_KEY` 进入

### 本地预览（可选）

```bash
source .venv/bin/activate
pip install -e ".[web]"
export ADMIN_KEY='test-password' SUPABASE_URL='https://xxx.supabase.co' SUPABASE_SERVICE_KEY='sbp_xxx'
python scripts/build_web_config.py
cd web/dist && python -m http.server 8000
# 打开 http://localhost:8000
```

