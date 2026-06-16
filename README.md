# Telegram PhotoBot Manager

基于 Docker 容器化部署的 Telegram 机器人管理及图床图片管理系统。集成 TG 机器人后台管理与 TG 图床上传、图片资源管理两大核心能力，支持双数据库切换策略与双 API 兼容方案。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | SQLite（默认）/ MySQL 8.0+（备用容灾） |
| 部署 | Docker + Docker Compose |
| 反向代理 | Nginx |

## 快速开始

### 环境要求

- Docker 20.0+
- Docker Compose 2.0+
- 服务器最低配置：1核 2G 内存
- 开放端口：**19533**（TCP）

### 1. 克隆项目

```bash
git clone https://github.com/ichq1069/telegram-photoBot
cd telegram-photoBot
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，修改以下配置：

```bash
# 必改项
SECRET_KEY=your-random-secret-key-here

# TG API 模式: official(官方) / self_build(自建中转)
TG_API_MODE=official

# MySQL 远程数据库（可选，用于容灾备份。留空则仅使用本地 SQLite）
MYSQL_HOST=
MYSQL_PORT=3306
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=photobot
```

### 3. 一键部署

```bash
docker compose up -d
```

### 4. 访问后台

浏览器打开 `http://<服务器IP>:19533`

- 默认账号：`admin`
- 默认密码：`admin123`

首次登录后请立即修改密码。

## Docker Compose 编排说明

```
服务架构：
                  ┌──────────┐
  用户 ── :19533 ──→│  Nginx   │── 静态文件 ── 前端页面
                  │  (80)    │
                  │          │── /api 代理 ──→ backend:8000
                  └──────────┘

  数据持久化：
  photobot_data volume ←→ 容器内 /app/data
  ├── photobot.db        (SQLite 数据库)
  ├── uploads/           (上传的图片文件)
  ├── thumbnails/        (缩略图)
  └── logs/              (应用日志)
```

### 容器运维命令

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 停止所有服务
docker compose down

# 重启所有服务
docker compose restart

# 查看运行日志
docker compose logs -f

# 查看后端日志
docker compose logs -f backend

# 查看运行状态
docker compose ps

# 更新镜像并重启
docker compose pull
docker compose up -d --force-recreate
```

### 端口说明

| 端口 | 用途 | 暴露范围 |
|------|------|----------|
| 19533 | Web 对外服务端口 | 公网 |
| 8000 | 后端 API（容器内部） | 仅容器间 |

服务器防火墙/安全组需放行 **19533** 端口 TCP 协议。如果端口被占用，排查命令：

```bash
netstat -tulpn | grep 19533
```

## 功能模块

### Telegram 机器人管理

- 多机器人绑定、分组管理
- 官方 API / 自建中转 API 自由切换
- 一键连通性检测、在线状态监控
- 自动回复、关键词回复、欢迎语配置
- 批量消息推送（文本/图片/文件）
- 消息日志记录与检索

### TG 图床上传与管理

- Web 端拖拽/点击上传，支持批量多图
- 图片自动压缩、格式转换
- 上传至 TG 频道/群组托管存储
- 自动生成直链、Markdown、BBCode 外链
- 缩略图预览、分类标签管理
- 访问统计、公开/私密切换

### 系统管理

- 仪表盘：服务器资源监控 + 上传统计
- 数据库：SQLite/MySQL 一键切换、手动同步
- 用户管理：多子账号、角色权限分级
- 配置中心：所有参数后台可视化配置
- 日志查询：多维度筛选检索

## 数据库容灾

```
默认模式：读写本地 SQLite
定时同步 → 远程 MySQL（可配置同步间隔）
故障切换：MySQL 不可用时自动回切 SQLite
手动切换：后台一键切换主库
```

## 安全配置

- JWT 令牌认证，密码 bcrypt 加密存储
- 上传文件格式/大小校验
- 图片外链支持过期时间、密码保护
- 单 IP 访问频率限制

## 目录结构

```
telegram-photobot/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # 配置、数据库、安全
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # 请求/响应模型
│   │   └── services/        # 业务逻辑层
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── api/             # Axios + API 端点
│   │   ├── layouts/         # 页面布局
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   └── views/           # 页面组件
│   ├── nginx.conf           # Nginx 配置
│   ├── vite.config.js       # Vite 配置
│   └── Dockerfile
├── docker-compose.yml       # Docker Compose 编排
├── .env.example             # 环境变量模板
├── start-dev.sh             # 本地开发脚本
└── .gitignore
```
