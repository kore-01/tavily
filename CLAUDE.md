# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TavilyProxy 是一个透明的 Tavily API 反向代理服务，将多个 Tavily API Key 汇聚在单一 Master Key 之后，并提供内置 Web UI 用于管理 Key、用量统计和请求日志。

**技术栈**:
- Backend: Go 1.23+ with Gin web framework
- Frontend: Vue 3 + Naive UI + Vite + TypeScript
- Database: SQLite (via GORM + glebarez/sqlite)
- Protocol: REST API + MCP (Model Context Protocol)

## Common Commands

### Development
```bash
# Start backend (from project root)
go run ./server

# Start frontend development server
cd web && npm install && npm run dev

# Run tests
go test ./server/...
```

### Build
```bash
# Windows
.\scripts\build_all.ps1

# Linux/macOS
./scripts/build_all.sh
```

### Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker logs tavily-proxy 2>&1 | grep "master key"
```

## Architecture

```
server/
├── main.go              # Entry point, service initialization
└── internal/
    ├── config/           # Environment configuration
    ├── db/               # Database connection & migrations
    ├── httpserver/       # HTTP router, handlers, middleware
    ├── jobs/             # Background scheduled tasks
    ├── logger/           # Daily rotating log writer
    ├── mcpserver/        # MCP protocol handler
    ├── models/           # GORM data models
    ├── services/         # Business logic layer
    │   ├── key_service.go       # API key pool management
    │   ├── tavily_proxy.go      # Proxy logic & key rotation
    │   ├── quota_sync_service.go # Quota synchronization
    │   └── ...
    └── util/             # Utilities (API key masking)

web/
├── src/
│   ├── api/              # HTTP client (Axios)
│   ├── components/       # Vue components
│   ├── views/            # Page views (Dashboard, KeyManagement, Logs, Settings)
│   └── ...
```

## Key Pool Strategy

The proxy uses a smart key selection algorithm:
1. **Priority**: Select key with highest remaining quota
2. **Load balancing**: Randomize among keys with equal quota
3. **Auto failover**: Automatically switch on 401/429/432/433 errors

## API Authentication

- Master Key via `Authorization: Bearer <MASTER_KEY>` header
- Also supports `api_key` in JSON body or query string
- First run generates Master Key automatically (check logs)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LISTEN_ADDR` | Server address | `:8080` |
| `DATABASE_PATH` | SQLite path | `./server/data/app.db` |
| `TAVILY_BASE_URL` | Upstream API | `https://api.tavily.com` |
| `UPSTREAM_TIMEOUT` | Proxy timeout | `150s` |
| `MCP_STATELESS` | MCP mode | `true` |
| `LOG_DIR` | Log directory | (stdout only) |
| `LOG_LEVEL` | Log level | `info` |
