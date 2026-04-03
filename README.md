# Tavily 代理池 & 管理面板

简体中文 | [English](./README_EN.md)

一个透明的 Tavily API 反向代理：将多个 Tavily API Key（额度/credits）汇聚在一个 **Master Key** 之后，并提供内置 Web UI 用于管理 Key、用量与请求日志。

---

## 🚀 功能特性

- **透明代理**：完整转发至 `https://api.tavily.com`（支持所有路径与方法）。
- **Master Key 鉴权**：客户端通过 `Authorization: Bearer <MasterKey>` 安全访问。
- **智能 Key 池管理**：
  - 优先使用剩余额度最高的 Key。
  - 同额度 Key 随机打散，有效防止请求过于集中触发频率限制。
- **自动故障切换**：遇到 `401` / `429` / `432` / `433` 等错误时，自动尝试 Key 池中的下一个可用 Key。
- **MCP 支持**：内置 HTTP MCP (Model Context Protocol) 端点，可轻松接入 Claude、VS Code 等 AI 工具。
- **可视化管理面板**：
  - **Key 管理**：便捷添加、删除及同步多个 Tavily Key 的额度信息。
  - **用量统计**：通过图表直观展示请求量与额度消耗趋势。
  - **请求日志**：详细记录每次请求，支持过滤筛选与手动清理。
- **自动化任务**：每月 1 号自动重置额度，定期清理历史日志。
- **开箱即用**：Go 二进制单文件部署，内嵌 Web UI（Vite + Vue 3 + Naive UI）。

---

## 🔑 Key 轮转策略详解

TavilyProxy 采用智能 Key 池管理策略，确保高可用性和公平性：

### 候选 Key 筛选条件

只有同时满足以下条件的 Key 才会被选中：
- ✅ `is_active = true` — Key 处于激活状态
- ✅ `is_invalid = false` — Key 未被标记为无效
- ✅ `used_quota < total_quota` — 还有剩余额度

### 排序与负载均衡

```
1. 按剩余额度（total - used）降序排序
2. 剩余额度相同的 Key 组内随机打乱（公平性）
```

**示例**：

| Key | 总额度 | 已用 | 剩余 | 排序结果 |
|-----|--------|------|------|----------|
| A | 1000 | 200 | 800 | 第 1 位（随机） |
| B | 1000 | 200 | 800 | 第 2 位（随机） |
| C | 500 | 100 | 400 | 第 3 位 |
| D | 500 | 400 | 100 | 第 4 位 |

### 故障自动切换

按排序后的顺序依次尝试，遇到不同错误有不同的处理策略：

| 状态码 | 处理方式 | Key 状态变化 |
|--------|----------|--------------|
| `200 OK` | 成功返回，停止尝试 | `used_quota++`（仅非 GET 请求） |
| `401 Unauthorized` | Key 失效，尝试下一个 | 标记 `is_invalid = true` |
| `429 TooManyRequests` | 临时限流，尝试下一个 | **不标记失效**，所有 Key 都 429 时返回最后一个 429 响应 |
| `432/433` | 额度耗尽，尝试下一个 | 标记 `used_quota = total_quota` |
| 网络错误 | 记录日志，尝试下一个 | 无变化 |

### 设计亮点

1. **优先级公平**：剩余额度高的优先使用，同额度随机打散避免集中
2. **429 特殊处理**：限速不废 Key，避免误杀临时受限的 Key
3. **零中断切换**：单个 Key 失败自动尝试下一个，客户端无感知
4. **自动状态管理**：401/432/433 自动标记，无需人工干预

---

## 🛠️ 环境要求

- **Docker / Docker Compose** (推荐部署方式，无需本地环境)
- **Go**: `1.23+` & **Node.js**: `20+` (仅用于本地手动编译)

---

## 📦 快速部署 (Docker)

直接使用 GHCR 镜像部署，**无需本地编译**。

### 1. 使用 Docker Compose (推荐)

创建 `docker-compose.yml` 文件：

```yaml
version: "3.8"
services:
  tavily-proxy:
    image: ghcr.io/kore-01/tavily:latest
    container_name: tavily-proxy
    ports:
      - "5050:5050"
    environment:
      - LISTEN_ADDR=:5050
      - DATABASE_PATH=/app/data/proxy.db
      - TAVILY_BASE_URL=https://api.tavily.com
      - UPSTREAM_TIMEOUT=30s
    volumes:
      - ./data:/app/data
      - /etc/localtime:/etc/localtime:ro
    restart: unless-stopped
```

执行启动：

```bash
docker-compose up -d
```

### 2. 使用 Docker 原生命令

```bash
docker run -d \
  --name tavily-proxy \
  -p 5050:5050 \
  -v $(pwd)/data:/app/data \
  -e DATABASE_PATH=/app/data/proxy.db \
  ghcr.io/kore-01/tavily:latest
```

---

## 🔑 首次运行：获取 Master Key

服务在**首次启动**时会自动生成一个随机的 **Master Key**，用于后续登录管理面板和调用 API。

您可以通过以下命令查看控制台日志来获取它：

```bash
docker logs tavily-proxy 2>&1 | grep "master key"
```

**日志示例：**
`level=INFO msg="no master key found, generated a new one" key=your_generated_master_key_here`

> **提示**：建议首次登录后在管理面板或通过数据库备份妥善保存此 Key。

---

## 🛠️ 本地开发与手动编译

如果您需要修改源码并自行构建：

1.  **启动后端**:
    ```bash
    go run ./server
    ```
2.  **启动前端**:
    ```bash
    cd web && npm install && npm run dev
    ```

**手动编译二进制产物**:

- **Windows**: `.\scripts\build_all.ps1`
- **Linux/macOS**: `./scripts/build_all.sh`

**使用 Dockerfile 构建镜像（Buildx）**:

首次使用可先初始化 Buildx：

```bash
docker buildx create --use
```

本地构建（当前主机架构）：

```bash
docker buildx build --load -t my-tavily-proxy .
```

构建并推送多架构镜像（`amd64` + `arm64`）：

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/<owner>/<repo>:latest \
  --push .
```

---

## 📖 使用指南

### REST API 代理

客户端调用方式与 Tavily 官方 API 完全一致，只需将 API 地址替换为代理地址，并使用 **Master Key**：

```bash
curl -X POST "http://localhost:5050/search" \
  -H "Authorization: Bearer <MASTER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"query": "最新 AI 技术趋势", "search_depth": "basic"}'
```

**兼容性说明**:

- 支持 `{"api_key": "<MASTER_KEY>"}` 或 `{"apiKey": "<MASTER_KEY>"}`。
- 支持 GET 参数 `?api_key=<MASTER_KEY>`。

### MCP (Model Context Protocol)

服务在 `http://localhost:5050/mcp` 提供 MCP 端点，**同时兼容 SSE 和 HTTP 两种传输模式**：

| 方法 | 模式 | 说明 |
|------|------|------|
| `GET` | SSE | 建立服务器推送流，适合长连接场景 |
| `POST` | HTTP Streamable | 无状态请求/响应，适合短连接场景 |

默认启用无状态模式（`MCP_STATELESS=true`），可避免客户端出现 `session not found` 错误。
如需有状态会话，请将 `MCP_STATELESS=false`，并确保上游反向代理正确透传 `Mcp-Session-Id` 且启用会话粘性（sticky）。

#### VS Code 配置示例 (配合 mcp-remote)

```json
{
  "servers": {
    "tavily-proxy": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:5050/mcp",
        "--header",
        "Authorization: Bearer 您的_MASTER_KEY"
      ]
    }
  }
}
```

---

## ⚙️ 配置项 (环境变量)

| 变量名             | 说明                 | 默认值                   |
| :----------------- | :------------------- | :----------------------- |
| `LISTEN_ADDR`      | 服务监听地址         | `:5050`                  |
| `DATABASE_PATH`    | SQLite 数据库路径    | `/app/data/proxy.db`     |
| `TAVILY_BASE_URL`  | 上游 Tavily API 地址 | `https://api.tavily.com` |
| `UPSTREAM_TIMEOUT` | 上游请求超时时间     | `150s`                   |
| `MCP_STATELESS`    | MCP 是否无状态模式   | `true`                   |
| `MCP_SESSION_TTL`  | MCP 会话空闲超时     | `10m`                    |

---

## 📄 开源协议

本项目基于 MIT 协议开源。
