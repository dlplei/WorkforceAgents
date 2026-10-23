# Workforce Operations Agent - Production MVP

智能员工服务与人力运营 Agent，基于容器化微服务（PostgreSQL + Chroma + Ollama BGE）与 FastAPI + React 的全栈实现。

## 架构

```
┌─────────────────┐         ┌────────────────────────────────────────────────────────┐
│   React 前端    │  SSE    │                  FastAPI 后端 (Python)                 │
│   (Vite + TS)   │ ◄─────► │                                                        │
│                 │         │  ┌──────────────────────────────────────────────────┐  │
│  - 对话界面     │         │  │           LangGraph 状态工作流 (StateGraph)      │  │
│  - 状态节点流转 │         │  │                                                  │  │
│    (4-Stage UI) │         │  │  [knowledge_retrieval] ──► [reasoning]           │  │
│  - 流式文本输出 │         │  │                                 │     ▲          │  │
│  - 工具调用展开 │         │  │                                 ▼     │          │  │
│                 │         │  │                         [tool_execution]         │  │
│                 │         │  │                                 │ (完成/流式回复) │  │
│                 │         │  │                                 ▼                │  │
│                 │         │  │                       [response_generation]      │  │
│                 │         │  └──────────────────────────────────────────────────┘  │
│                 │         │  - astream_events(v2) 全双工事件翻译                    │
│                 │         │  - Tool Registry (9大 HR 运维工具)                      │
│                 │         │  - RAG 向量知识库 (ChromaDB + Ollama BGE-M3 / 本地降级)  │
│                 │         │  - PostgreSQL 18 持久化 & Mock 数据                    │
└─────────────────┘         └───────────────────────────┬────────────────────────────┘
                                                        │
                                                        ▼
                                            ┌─────────────────────┐
                                            │  OpenAI 兼容 API    │
                                            │  (LLM 推理服务)     │
                                            └─────────────────────┘
```

## 项目结构

```
.
├── backend/                     # Python 后端
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理与环境变量
│   ├── models.py               # Pydantic 数据模型
│   ├── mock_data.py            # HR Mock 数据
│   ├── requirements.txt        # Python 依赖（含 LangGraph, LangChain）
│   ├── test_agent_regression.py # Agent 与 LangGraph 端到端回归测试
│   └── agent/
│       ├── graph.py            # LangGraph 状态机定义与工作流编排 (StateGraph)
│       ├── engine.py           # Agent 核心引擎 (LangGraph 事件桥接与 SSE 转化)
│       ├── knowledge.py        # 向量/关键词混合 RAG 知识检索
│       ├── tools.py            # Tool Registry 工具注册中心
│       └── ingest_knowledge.py # 知识库切片与向量入库脚本
│
├── src/                         # React 前端
│   ├── App.tsx                 # 主应用组件
│   ├── config.ts               # 前端配置
│   ├── types.ts                # TypeScript 类型定义与 SSE 协议声明
│   └── components/
│       ├── ChatInterface.tsx   # 聊天界面（支持 4 阶段节点流转动画展示）
│       ├── Sidebar.tsx         # 侧边栏与快速功能入口
│       └── SettingsModal.tsx   # 设置面板
│
└── README.md
```


## 容器基础设施与数据库 (Podman / Docker)

本系统采用生产级容器化微服务：
- **PostgreSQL 18-alpine** (5432): 持久化员工档案、假期余额、日历日程、审批流与 HR 服务工单；
- **Chroma 向量数据库** (8000): 存储企业 HR 政策与规章制度的密集向量切片；
- **Ollama BGE-M3** (11434): 本地 1024 维密集语义向量生成模型。

```bash
# 启动持久化容器服务
podman-compose up -d

# 将企业政策知识库切片并向量化写入 Chroma
python backend/agent/ingest_knowledge.py
```

### HR 适配器可插拔架构 (IHRServiceAdapter)
支持通过环境变量无缝切换数据源：
- `HR_ADAPTER_TYPE=local`：默认，使用本地 PostgreSQL 存储 HR 数据；
- `HR_ADAPTER_TYPE=servicenow`：对接企业 ServiceNow PDI 实例（Table API / Incident / HR Case），并自动向本地 PostgreSQL 双写缓存。

## 快速开始

### 1. 配置后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key 等配置
```

**重要：编辑 `.env` 文件**

```bash
# 必填：你的 LLM API Key
LLM_API_KEY=sk-your-actual-api-key-here

# 可选：修改 Base URL（如果使用非 OpenAI 的兼容服务）
LLM_BASE_URL=https://api.openai.com/v1

# 可选：修改模型
LLM_MODEL=gpt-4o-mini
```

### 2. 启动后端

```bash
# 启动服务
python main.py
# 或
uvicorn main:app --reload --port 8000
```

后端将在 `http://localhost:8000` 启动。启动时会显示配置信息日志。

### 3. 启动前端

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 或构建生产版本
npm run build
```

前端将在 `http://localhost:5173` 启动（开发模式）。

### 4. 配置前端

打开浏览器访问前端地址（http://localhost:5173），首次使用会弹出设置面板：

**重要：需要区分两个 URL**

- **后端地址 (Backend URL)**: `http://localhost:8000`
  - 这是本地 FastAPI 后端的地址
  - 前端通过这个地址与后端通信
  
- **LLM API 地址 (LLM Base URL)**: `https://api.servicesessentials.ibm.com/v1`
  - 这是你的 LLM 服务地址
  - 前端会把这个地址传给后端，后端再用它调用 LLM

- **API Key**: 你的 LLM API Key
- **模型**: 如 `gpt-4o-mini`, `gpt-4o` 等

**注意**：
- 前端配置会覆盖后端 .env 配置
- 如果前端不填写配置，将使用后端 .env 中的默认值
- **不要把 LLM API 地址填到后端地址字段！**

## 功能特性

### Agent 能力

- ✅ **政策咨询**: 查询公司各项 HR 政策
- ✅ **休假管理**: 查询假期余额、协助请假申请
- ✅ **差旅管理**: 计算差旅预算
- ✅ **证明开具**: 协助开具各类证明
- ✅ **信息查询**: 查询员工信息、审批状态

### 技术特性

- ✅ **LangGraph 状态图工作流**: 基于 StateGraph 的显式状态机循环编排，天然支持 Subgraph 嵌套无缝升级多 Agent Supervisor 架构
- ✅ **4 阶段状态生命周期**: 前后端协同呈现 `knowledge_retrieval` ➔ `reasoning` ➔ `tool_execution` ➔ `response_generation` 阶段流转
- ✅ **Tool Calling**: 9 个自主与确认型运维工具（假期、差旅、证明、日程、工单草稿等）
- ✅ **混合 RAG 知识库**: Chroma 密集向量检索（Ollama BGE-M3 1024 维）+ 本地关键词检索自动容灾降级
- ✅ **标准流式事件协议**: 基于 LangGraph `astream_events(version="v2")` 的全双工实时事件翻译与 SSE 传输
- ✅ **权限边界与安全审查**: 工具权限分级（自主执行/需用户二次确认/高风险受限），支持敏感操作人机协同
- ✅ **企业系统适配器**: 支持本地 PostgreSQL 18 与企业级 ServiceNow PDI 实例无缝切换

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
- `node_enter`: 进入工作流阶段节点（如 `knowledge_retrieval`, `reasoning`, `tool_execution`, `response_generation`）
- `node_exit`: 退出工作流阶段节点
- `tool_call`: 工具调用触发（包含函数名与参数）
- `tool_result`: 工具执行结果返回
- `token`: 文本逐字流式 token
- `message_complete`: 单轮消息处理完成
- `error`: 异常报错
- `status`: 状态变化（如 start, done, error）

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

### Phase 1 (核心基础设施与 Agent 架构升级 - 已完成)
- [x] **Agent 架构升级为 LangGraph**: 使用 StateGraph 状态机重构编排引擎，支持细粒度事件生命周期监控
- [x] **向量检索与 RAG 强化**: 接入 ChromaDB 向量数据库与 Ollama BGE-M3 (1024维密集语义嵌入)，支持本地容灾降级
- [x] **数据持久化**: 接入 PostgreSQL 18-alpine 持久化员工、假期、日程、工单与审批数据
- [x] **企业级 HRIS 适配器**: 实现可插拔 `IHRServiceAdapter` 架构，支持对接企业 ServiceNow PDI 实例并本地双写缓存
- [ ] 添加 Prometheus + Grafana 指标监控与遥测追踪

### Phase 2 (多 Agent 与企业生态扩展)
- [ ] **多 Agent Supervisor 协作**: 直接利用 LangGraph Subgraph 特性，将当前 Workforce Graph 作为子图挂载至主管 Agent 下，扩展差旅专家 Agent、IT 运维 Agent
- [ ] **接入真实企业 IM**: 钉钉 / 飞书 / 企业微信 / Teams 机器人 Webhook 联动
- [ ] **主动服务推送**: 政策变动、假期到期提醒、审批待办通知
- [ ] **安全审计与合规**: 全链路敏感数据脱敏与操作审计日志

## 技术栈

**前端**:
- React 18 + TypeScript
- Vite
- Tailwind CSS + Lucide Icons

**后端**:
- FastAPI + Uvicorn
- **LangGraph** (StateGraph 状态工作流编排)
- **LangChain Core** & **LangChain OpenAI**
- Pydantic v2
- httpx (全异步 HTTP 客户端)
- SSE-Starlette (Server-Sent Events 流式分发)
- ChromaDB Client + Ollama (密集向量检索)
- PostgreSQL 18 (数据持久化)

**LLM & Embedding**:
- 支持 OpenAI 兼容协议（GPT-4o, GPT-4o-mini, Claude, 本地模型等）
- BGE-M3 (本地 1024 维 Embedding 模型)

## License

MIT

# 以下作为参考


### 核心问题解答：按方案 B 实施后，升级到方案 C（多 Agent Supervisor 架构）容易吗？

**结论：非常容易，而且方案 B 正是演进到方案 C 的“黄金标准”与最佳垫脚石（Subgraph 子图设计哲学）。**

具体原因与演进路径如下：

1. **LangGraph 的核心特性：“图即节点”（Graph as a Node）**
   - 在 LangGraph 中，任何一个编译好的状态图（`CompiledGraph`）都可以**直接当作另一个父图的节点（Node）来调用**。
   - 我们刚刚构建的 `workforce_graph`，在升级到多 Agent Supervisor 时，**内部节点和业务逻辑一行都不用改**，直接作为父图的一个专用子图挂载：
     ```python
     # 方案 C 架构示例（平滑升级，直接复用方案 B）：
     supervisor_graph = StateGraph(SupervisorState)
     supervisor_graph.add_node("supervisor", supervisor_router_node)
     supervisor_graph.add_node("hr_agent", hr_operations_subgraph)       # 方案 B 原封不动挂载为子图
     supervisor_graph.add_node("travel_agent", travel_expert_subgraph)   # 未来新增的差旅专家子图
     supervisor_graph.add_node("it_support_agent", it_support_subgraph) # 未来新增的 IT 运维子图
     ```

2. **状态共享与隔离（State Scoping）完全解耦**
   - 方案 B 中定义的 `AgentState` 拥有标准的 `messages`、`retrieved_docs` 等通道。
   - 升级到 Supervisor 架构时，Supervisor 负责全局路由与多 Agent 结果汇总，各个专项子图 Agent 在自己的上下文中执行工具，避免单一 Agent 上下文过载和工具互相污染。

3. **前端 SSE 协议平滑无感升级**
   - 方案 B 已经把底层流式事件全部标准化为 `node_enter`、`tool_call`、`tool_result`、`token` 等前端原生支持的格式。
   - 在 Supervisor 架构下，`astream_events(version="v2")` 会自动穿透并标记事件来源（带有 sub-graph namespace），前端不仅无需改动既有渲染结构，还能更细致地在界面上展示当前是哪一个专项专家 Agent 正在工作。

---

### 方案 B 实施完成情况汇总

已按规划成功将 `backend/agent/engine.py` 中的原生 ReAct while 循环重构为基于 **LangGraph StateGraph** 的企业级工作流架构：

#### 1. 依赖环境更新
- 在 `backend/requirements.txt` 中添加：
  - `langgraph>=0.2.20`
  - `langchain-core>=0.3.0`
  - `langchain-openai>=0.2.0`
- 完成环境依赖安装（包含底层数据库依赖 `psycopg[binary]` 与向量库支持）。

#### 2. 状态图编排实现 (`backend/agent/graph.py`)
- **状态定义 (`AgentState`)**：统一管理消息队列 `messages: Annotated[Sequence[BaseMessage], add_messages]` 及 RAG 政策切片 `retrieved_docs`。
- **动态 Prompt 构建 (`build_system_prompt`)**：将当前员工身份（张明 E10293）、系统年份与真实日期基准注入 System Message。
- **状态图节点**：
  - `knowledge_retrieval`：自动提取最新用户问题，检索本地/向量知识库。
  - `reasoning`：基于动态 Prompt 与政策知识，绑定 9 大 HR 运维工具，驱动 `ChatOpenAI` 推理。
  - `tool_execution`：接收模型 `tool_calls`，通过 `adispatch_custom_event` 派发细粒度工具事件，并安全执行工具。
- **条件边 (`should_continue`)**：精准判断是否需要执行工具还是流转至 `END` 完成流程。

#### 3. Agent 核心引擎重构 (`backend/agent/engine.py`)
- 移除了原有 200 余行复杂且脆弱的手工 HTTP 流解析代码（`_call_llm` 与 `_parse_stream`）。
- 采用 LangGraph 官方标准的 `graph.astream_events(version="v2")`，无缝对接前端 SSE 协议：
  - `node_enter` / `node_exit`（对应前端顶部的阶段标签卡片：`knowledge_retrieval`、`reasoning`、`tool_execution`、`response_generation`）。
  - `tool_call` / `tool_result`（实时推送到前端工具调用展开框）。
  - `token`（文本逐字平滑流式推送）。
  - `message_complete`（会话结束并持久化到多轮历史）。

#### 4. 全量回归测试验证
编写并运行了端到端回归测试脚本 `backend/test_agent_regression.py`，三个核心场景全部通过：
1. **政策咨询与 RAG 检索**：测试“年假政策规定与申请提前期”，自动检索《员工年假管理办法》（POL-001）并给出详尽合规回复。
2. **工具调用闭环**：测试“帮我查一下我目前的年假余额还剩几天？”，Agent 自动解析参数调用 `query_leave_balance`，执行成功后返回剩余 7 天并流式输出。
3. **多轮对话上下文延续**：测试跨轮次提问与追问，上下文历史记录无缝延续。