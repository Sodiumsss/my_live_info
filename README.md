# live_info

演唱会信息自动分发。详见 [设计文档](docs/superpowers/specs/2026-04-20-live-info-design.md)。

## 本地开发

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # 填入自己的 Secrets
pytest
```
