# 贡献指南

## 开发环境

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## 代码规范

- Python: 遵循 PEP 8，类型注解全覆盖
- TypeScript: strict 模式，`noUnusedLocals` / `noUnusedParameters` 检查
- 提交前确保 `npm run build` 通过

## 提交信息

```
<type>(<scope>): <description>

feat(ocr): add PaddleOCR client
fix(db): handle NULL stats query
docs(readme): update output format description
```

## 分支策略

- `main` — 稳定分支，需通过构建验证
- `feat/*` — 功能开发分支
- `fix/*` — 修复分支
