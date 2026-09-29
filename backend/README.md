# Backend (FastAPI + SQLAlchemy)

最小示例，包含 `materials` 和 `purchase_orders` 的 CRUD。

快速开始：

1. 创建虚拟环境并安装依赖：

```bash
python -m venv .venv
.venv\\Scripts\\activate  # Windows
pip install -r backend/requirements.txt
```

2. （可选）设置数据库连接（不设置则回退到 SQLite 文件 `./backend.db`）：

```bash
# 例如 MySQL
set DATABASE_URL=mysql+pymysql://user:pass@localhost/dbname
```

3. 运行开发服务器：

```bash
uvicorn backend.app:app --reload --port 8000
```

4. 打开交互式 API 文档：

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

备注:
- 生产环境请考虑连接池、事务边界、迁移工具（如 Alembic）及更严格的配置。
