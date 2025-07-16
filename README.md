# earth-server
AI地球项目的后台

# Earth Server 启动全流程

## 1. 环境准备

### 1.1 安装依赖
建议使用 Python 3.9+，并提前安装好 pip。

```sh
pip install -r requirements.txt
```

如需 micromamba/pip 混合环境，参考 `requirements.micromamba.txt` 和 `requirements.pip.txt`。

### 1.2 安装 MinIO、Redis、MySQL、Caddy
可通过系统包管理器或官方文档安装，或直接使用本项目的 `init.d` 脚本（见下文）。

## 2. 配置环境变量

在项目根目录下新建 `.env` 文件，内容示例：

```env
DATABASE_NAME=ai_earth
DATABASE_USER=super
DATABASE_PASSWORD=super
DATABASE_HOST=localhost
DATABASE_PORT=3306

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=ai-earth

CSRF_SECRET=your_csrf_secret
PUBLIC_BASE_URL=http://localhost
```

## 3. 启动基础服务

推荐使用 `init.d/backend` 脚本一键启动所有依赖服务：

```sh
sudo bash init.d/backend start
```

如需单独启动 MinIO、Redis、MySQL、Caddy，可分别运行 `init.d/` 目录下对应脚本。Caddy配置文件可见目录下。

## 4. 启动后端服务

### 4.1 命令行方式

在项目根目录下执行：

```sh
litestar run -rdH 0.0.0.0
```

如 litestar 未安装，请先激活虚拟环境并安装依赖。

### 4.2 VS Code 任务方式

在 VS Code 命令面板（Ctrl+Shift+P）输入 `Run Task`，选择 `Run litestar`。

## 5. 启动 Caddy 反向代理（可选）

如需通过 Caddy 提供 Web 入口，确保 `/etc/caddy/Caddyfile` 配置正确并启动 Caddy：

```sh
sudo systemctl restart caddy.service
```

## 6. 访问服务

后端 API 默认监听 `http://localhost:8000`，可根据 Caddy 配置通过 80/443 端口访问。

---

如遇问题请查看各服务日志，或联系开发者。
