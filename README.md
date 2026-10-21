# Workforce Operations Agent - MVP Demo

智能员工服务与人力运营 Agent，基于 FastAPI + React 的全栈实现。

## 架构

```
┌─────────────────┐         ┌─────────────────────┐
│   React 前端    │  SSE    │   FastAPI 后端      │
│   (Vite + TS)   │ ◄─────► │   (Python)          │
│                 │         │                     │
│  - 对话界面     │         │  - Agent 引擎       │
│  - 流式输出     │         │  - ReAct 循环       │
│  - 工具可视化   │         │  - Tool Calling     │
└─────────────────┘         │  - RAG 知识库       │
                            │  - Mock 数据        │
                            └──────────┬──────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │  OpenAI 兼容 API    │
                            │  (LLM 服务)         │
                            └─────────────────────┘
```

## 项目结构

```
.
├── backend/                 # Python 后端
│   ├── main.py             # FastAPI 入口
│   ├── config.py           # 配置管理
│   ├── models.py           # 数据模型
│   ├── mock_data.py        # Mock 数据
│   ├── requirements.txt    # Python 依赖
│   └── agent/
│       ├── engine.py       # Agent 核心引擎 (ReAct)
│       ├── knowledge.py    # RAG 知识库
│       └── tools.py        # Tool Calling 框架
│
├── src/                     # React 前端
│   ├── App.tsx             # 主应用
│   ├── config.ts           # 前端配置
│   ├── types.ts            # 类型定义
│   └── components/
│       ├── ChatInterface.tsx   # 对话界面
│       ├── Sidebar.tsx         # 侧边栏
│       └── SettingsModal.tsx   # 设置面板
│
└── README.md
```

## 快速开始

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 或
uvicorn main:app --reload --port 8000
```

后端将在 `http://localhost:8000` 启动。

### 2. 启动前端

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 或构建生产版本
npm run build
```

前端将在 `http://localhost:5173` 启动（开发模式）。

### 3. 配置 API

打开浏览器访问前端地址，首次使用会弹出设置面板：

- **后端地址**: `http://localhost:8000`
- **API Key**: 你的 OpenAI 兼容 API Key
- **模型**: 如 `gpt-4o-mini`, `gpt-4o` 等

## 功能特性

### Agent 能力

- ✅ **政策咨询**: 查询公司各项 HR 政策
- ✅ **休假管理**: 查询假期余额、协助请假申请
- ✅ **差旅管理**: 计算差旅预算
- ✅ **证明开具**: 协助开具各类证明
- ✅ **信息查询**: 查询员工信息、审批状态

### 技术特性

- ✅ **ReAct 循环**: 多步推理 + 工具调用
- ✅ **Tool Calling**: 8 个可插拔工具
- ✅ **RAG 知识库**: 7 篇 Mock 政策文档
- ✅ **流式输出**: SSE 实时传输
- ✅ **权限边界**: 工具分级（自主/确认/受限）
- ✅ **Mock 数据**: 员工、审批、日历数据

## API 接口

### POST /api/chat

聊天接口（流式 SSE）

**请求体**:
```json
{
  "message": "帮我查一下还有多少年假",
  "config": {
    "api_key": "sk-...",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

**响应**: Server-Sent Events 流

事件类型:
- `token`: 文本 token
- `tool_call`: 工具调用
- `tool_result`: 工具结果
- `message_complete`: 消息完成
- `error`: 错误
- `status`: 状态变化

### GET /api/tools

获取所有可用工具列表

### GET /api/employee

获取当前登录员工信息

## 测试场景

1. **查询假期余额**: "帮我查一下我还有多少年假"
2. **政策咨询**: "公司年假政策是怎样的？请3天以上需要怎么审批？"
3. **差旅预算**: "我下周要去上海出差3天，帮我算一下差旅预算"
4. **开具证明**: "我需要开一份在职证明，用于办理签证"
5. **请假申请**: "帮我请10月8日到10日的年假"

## 日志与调试

### 查看日志

后端会输出详细的日志信息，包括：

- 🚀 LLM API 调用信息（URL、模型、API Key）
- 📋 请求配置（温度、最大 token 数）
- 📨 响应状态码和响应头
- 🔧 工具调用详情
- 💥 完整错误堆栈

### 常见错误诊断

如果遇到 `LLM API 错误 (403): Connect failed` 等连接错误：

1. **查看详细日志**：后端控制台会输出完整的错误信息和诊断建议
2. **检查配置**：确认 Base URL、API Key、模型名称正确
3. **测试连接**：使用 curl 测试 LLM API 连接
4. **查看故障排除文档**：参考 `TROUBLESHOOTING.md`

### 调整日志级别

```python
# backend/main.py
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG/INFO/WARNING/ERROR
    ...
)
```

## 后续升级路径

### Phase 1
- [ ] 将关键词检索替换为向量检索（连接向量数据库）
- [ ] 将 Mock 员工数据替换为 HRIS API
- [ ] 将内存 Memory 替换为 PostgreSQL + Redis
- [ ] 添加 Prometheus + Grafana 监控

### Phase 2
- [ ] 接入真实 IM 系统（钉钉/飞书/Teams）
- [ ] 多 Agent 协作
- [ ] 主动服务推送
- [ ] 安全审计与合规

## 技术栈

**前端**:
- React 18 + TypeScript
- Vite
- Tailwind CSS

**后端**:
- FastAPI
- Pydantic
- httpx (HTTP 客户端)
- SSE-Starlette

**LLM**:
- OpenAI 兼容 API
- 支持 GPT-4o, GPT-4o-mini, Claude 等

## License

MIT
# WorkforceAgents

# 1. 安装依赖（必须）
npm install

# 2. 启动开发服务器
npm run dev
