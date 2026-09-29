部署指南（初稿）

示例：Docker Compose（开发/小规模自托管）
- 服务：`app`、`mysql`、`redis`
- 环境变量：数据库连接、密钥、汇率 API KEY（如有）

备份与恢复
- 使用 `mysqldump` 做定期备份，备份文件保存在挂载卷并定期同步到远程存储

部署步骤（简要）
1. 准备主机（2 核 4GB 起）
2. 拉取镜像并配置 `.env`
3. 启动：`docker-compose up -d`
4. 运行数据库迁移（Alembic/TypeORM）

快速启动脚本
- Windows PowerShell：`./scripts/start_erp.ps1`
- Linux/macOS：`./scripts/start_erp.sh`

监控建议
- 基础监控：CPU/内存/磁盘
- 应用层：错误率与慢查询监控