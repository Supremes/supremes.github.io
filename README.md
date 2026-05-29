  # 本地验证
  uv sync
  uv run build.py
  python3 -m http.server 8000 -d dist   # 浏览器看一眼