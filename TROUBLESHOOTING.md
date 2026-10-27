# 故障排除指南

## 快速定位：页面一直 "Waiting for 127.0.0.1:3000"（白屏不出画面）

> **最常见原因不是项目代码，而是浏览器/系统代理把本地请求劫持了。**
> 判断方法：在运行前端的同一台机器上执行 `curl -sI http://127.0.0.1:3000/`，
> 若**秒回 HTTP 200**，说明 Vite 服务本身没问题 → 请优先检查下面第 1 条（代理 bypass）。

详见下方 **0.9 节**（含完整排查清单与自检脚本）。

---

## 常见错误及解决方案

### 0.9 页面长时间白屏 / 浏览器一直显示 "Waiting for http://127.0.0.1:3000 ..."

**症状：**
`npm run dev` 和后端都正常启动（终端里能看到 `VITE v6.x ready`），但浏览器打开
`http://127.0.0.1:3000/` 或 `http://localhost:3000/` 时长时间不出画面，状态栏一直是
"Waiting for 127.0.0.1:3000…" / "正在等待站点响应"。

**按可能性从高到低排查：**

1. **浏览器/系统代理劫持了本地请求（最常见）**
   - 表现：`curl http://127.0.0.1:3000/` 秒回 200，但浏览器一直 Waiting；
     或 curl 走代理时也卡住。开了 Clash / v2rayN / 公司 PAC 代理时尤其常见。
   - 解决：把 `127.0.0.1`、`localhost`、`::1` 加入代理 **bypass（不使用代理的主机）** 列表；
     或临时关闭代理再刷新；或使用浏览器的无痕/直连配置档。
   - 命令行验证是否被代理影响：
     ```bash
     env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY        curl -sv -o /dev/null http://127.0.0.1:3000/
     ```
   - 本项目已在 `vite.config.js` 中加了 `/api` dev proxy，前端默认用**同源相对路径**
     请求后端（见下一条），可顺带消除跨域与二次代理问题。

2. **首次访问触发 Vite 依赖预打包（optimize deps）阻塞**
   - 表现：第一次打开慢，控制台出现
     `new dependencies optimized: react, react-dom, lucide-react ...` 后页面重新加载。
   - 若 `node_modules` 是中断/不完整安装留下的，预打包会一直失败重试 → 永远 Waiting。
   - 解决：
     ```bash
     rm -rf node_modules/.vite node_modules
     npm install
     npm run dev -- --force
     ```
   - 本项目已在 `vite.config.js` 的 `optimizeDeps.include` 中显式列出全部依赖，避免运行时才发现。

3. **只监听了 127.0.0.1，而 `localhost` 解析成 IPv6 `::1`**
   - 老配置 `server.host: "127.0.0.1"` + `hmr.host: "127.0.0.1"` 会导致
     `http://localhost:3000/` 连不上、HMR websocket 也连不上（表现为一直转圈）。
   - 现已改为 `host: true`（同时监听 IPv4/IPv6）+ `hmr.clientPort`，两种地址都能访问。
   - 注意：从其它机器/容器外访问时要用 `http://<宿主机IP>:3000/`，而不是 `localhost`。

4. **端口被别的进程占用**（`strictPort: true` 时 Vite 会直接报错退出，不会静默挂起）
   ```bash
   # Linux/macOS
   lsof -i :3000        # 或 ss -ltnp | grep 3000
   # Windows
   netstat -ano | findstr :3000
   ```

5. **前端把 LLM 地址填进了"后端地址"**（见 0.5 节）→ 请求打到远端不可达地址上长时间 pending。
   现在"后端地址"留空即可，前端会走同源 `/api/*` 由 Vite 转发到 `http://127.0.0.1:8000`。

**快速自检脚本（在服务器上跑，全部应为 200 且毫秒级返回）：**
```bash
for u in http://127.0.0.1:3000/ http://localhost:3000/ \
         http://127.0.0.1:3000/src/main.tsx \
         http://127.0.0.1:3000/node_modules/.vite/deps/react-dom_client.js \
         http://127.0.0.1:3000/api/tools; do
  echo -n "$u -> "; curl -s -m 10 -o /dev/null -w "%{http_code} %{time_total}s\n" "$u"
done
```
如果这些都快、只有浏览器慢，那 100% 是浏览器侧的代理/扩展/DNS 问题，与项目代码无关。

### 0.5. CORS 错误 / NetworkError（配置混淆）

**症状：**
```
Cross-Origin Request Blocked: The Same Origin Policy disallows reading the remote resource at https://api.servicesessentials.ibm.com/v1/api/tools
❌ 错误：NetworkError when attempting to fetch resource.
```

**原因：**
前端把 **LLM API 地址** 填到了 **后端地址** 字段，导致前端直接访问 LLM API 而不是本地后端。

**解决方案：**

1. **打开前端设置面板**（点击右上角齿轮图标）

2. **正确填写两个 URL：**
   ```
   后端地址 (Backend URL): http://localhost:8000
   LLM API 地址 (LLM Base URL): https://api.servicesessentials.ibm.com/v1
   ```

3. **关键区别：**
   - **后端地址** = 本地 FastAPI 服务（`http://localhost:8000`）
   - **LLM API 地址** = 你的 LLM 服务（IBM/OpenAI 等）

4. **保存配置并刷新页面**

**验证方法：**
- 打开浏览器开发者工具 → Network 标签
- 应该看到请求发往 `http://localhost:8000/api/tools` 和 `http://localhost:8000/api/chat`
- 而不是直接访问 LLM API 地址

### 0. 配置未加载 / API Key 未配置

**症状：**
```
⚠️  未找到 .env 文件
❌ 未配置 API Key
```

**解决方案：**

1. **创建 .env 文件**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **编辑 .env 文件**
   ```bash
   # 必填：你的 LLM API Key
   LLM_API_KEY=sk-your-actual-api-key-here
   
   # 可选：修改其他配置
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4o-mini
   LLM_TEMPERATURE=0.7
   LLM_MAX_TOKENS=2048
   ```

3. **测试配置加载**
   ```bash
   python test_config.py
   ```

4. **重启后端服务**
   ```bash
   python main.py
   ```

**注意：**
- `.env` 文件不会被提交到 git（已在 .gitignore 中）
- 前端配置会覆盖后端 .env 配置
- 如果前端不填写配置，将使用后端 .env 中的默认值

### 1. LLM API 错误 (403): Connect failed

**症状：**
```
❌ LLM API 错误 (403): Connect failed
```

**可能原因：**

1. **Base URL 配置错误**
   - 检查前端配置中的 Base URL 是否正确
   - 常见错误：缺少 `/v1` 后缀或多了斜杠
   - 正确示例：`https://api.openai.com/v1`

2. **网络连接问题**
   - 后端服务器无法访问 LLM API
   - 可能是防火墙、代理或网络限制
   - 测试命令：
     ```bash
     curl -v https://api.openai.com/v1/models \
       -H "Authorization: Bearer YOUR_API_KEY"
     ```

3. **API Key 无效或过期**
   - 检查 API Key 是否正确
   - 确认账户有足够余额
   - 检查 API Key 权限

4. **需要代理但未配置**
   - 如果在中国大陆访问 OpenAI，需要配置代理
   - 在启动后端前设置环境变量：
     ```bash
     export HTTP_PROXY=http://proxy:port
     export HTTPS_PROXY=http://proxy:port
     ```

5. **LLM API 服务不可用**
   - 检查 LLM 服务商的状态页面
   - 尝试使用其他模型（如 gpt-4o-mini → gpt-4o）

**诊断步骤：**

1. 查看后端日志，找到详细的错误信息：
   ```bash
   # 后端会输出类似以下的日志
   🚀 调用 LLM API: https://api.openai.com/v1/chat/completions
   📋 模型: gpt-4o-mini
   🔑 API Key: sk-1234...5678
   🔌 连接错误: ...
   ```

2. 检查后端日志中的完整错误堆栈

3. 手动测试 API 连接：
   ```bash
   cd backend
   python -c "
   import httpx
   import asyncio
   
   async def test():
       async with httpx.AsyncClient() as client:
           try:
               resp = await client.get(
                   'https://api.openai.com/v1/models',
                   headers={'Authorization': 'Bearer YOUR_API_KEY'},
                   timeout=10.0
               )
               print(f'Status: {resp.status_code}')
               print(f'Response: {resp.text[:200]}')
           except Exception as e:
               print(f'Error: {e}')
   
   asyncio.run(test())
   "
   ```

### 2. 前端无法连接后端

**症状：**
```
无法加载工具列表
```

**解决方案：**

1. 确认后端已启动：
   ```bash
   curl http://localhost:8000/
   # 应返回: {"status":"ok","service":"Workforce Operations Agent","version":"0.1.0"}
   ```

2. 检查 CORS 配置（backend/main.py）：
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 开发环境
       # 生产环境应限制为具体域名
       # allow_origins=["http://localhost:5173"],
   )
   ```

3. 检查浏览器控制台的网络请求

### 3. Agent 无法调用工具

**症状：**
Agent 回复中没有调用工具，或工具调用失败

**解决方案：**

1. 检查工具是否正确注册：
   ```bash
   curl http://localhost:8000/api/tools
   ```

2. 查看后端日志中的工具调用记录

3. 检查 LLM 是否正确返回 tool_calls

### 4. 流式输出中断

**症状：**
回复到一半就停止了

**可能原因：**

1. **max_tokens 设置过小**
   - 增加 max_tokens 配置

2. **网络连接不稳定**
   - 检查网络状况
   - 查看后端日志是否有超时错误

3. **LLM API 限制**
   - 检查速率限制
   - 查看是否有并发请求限制

## 日志级别调整

### 临时调整（推荐用于调试）

修改 `backend/main.py`：
```python
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 获取更详细日志
    ...
)
```

修改 `backend/agent/engine.py`：
```python
logger.setLevel(logging.DEBUG)
```

### 使用环境变量

```bash
# Linux/Mac
export LOG_LEVEL=DEBUG
python main.py

# Windows
set LOG_LEVEL=DEBUG
python main.py
```

## 获取帮助

如果以上方法都无法解决问题，请提供以下信息：

1. 完整的后端日志输出
2. 前端配置截图（隐藏 API Key）
3. 网络测试结果（curl 命令输出）
4. 操作系统和环境信息

## 性能优化建议

1. **调整日志级别**
   - 生产环境使用 WARNING 或 ERROR
   - 开发环境使用 INFO 或 DEBUG

2. **启用日志文件**
   ```python
   logging.basicConfig(
       handlers=[
           logging.StreamHandler(),
           logging.FileHandler('agent.log'),  # 添加文件输出
       ]
   )
   ```

3. **结构化日志**
   - 考虑使用 JSON 格式的日志
   - 便于日志收集和分析
