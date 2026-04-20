# live_info admin web

Vite + Vue 3 + TypeScript + Tailwind + shadcn-vue 风格组件，部署到 GitHub Pages。

## 通讯架构

不依赖任何后端：构建时由 `scripts/build_web_config.py` 用 `ADMIN_KEY` 把 `SUPABASE_SERVICE_KEY` 通过 PBKDF2 + AES-GCM 加密成 `dist/config.js`（只含密文）。前端在登录页用浏览器 `crypto.subtle` 解密，拿到 service key 后直接用 `@supabase/supabase-js` 调 Supabase REST API。

## 本地开发

```bash
cd web
npm install
# 用本地脚本生成一份 config.js 放到 public/（开发时不入库）
ADMIN_KEY=test \
  SUPABASE_URL=https://x.supabase.co \
  SUPABASE_SERVICE_KEY=your-service-key \
  WEB_DIST=public \
  python ../scripts/build_web_config.py
npm run dev
```

## 生产构建

```bash
cd web
npm ci
npm run build
# 然后在仓库根目录跑（CI 已经串好）：
ADMIN_KEY=... SUPABASE_URL=... SUPABASE_SERVICE_KEY=... \
  python scripts/build_web_config.py
```

GitHub Actions 工作流：[.github/workflows/pages.yml](../.github/workflows/pages.yml)。
