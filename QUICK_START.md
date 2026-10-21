# 快速配置指南

## ⚠️ 重要：理解两个 URL 的区别

前端设置中有两个容易混淆的 URL 字段：

### 1. 后端地址 (Backend URL)
```
http://localhost:8000
```
- **这是什么**：本地 FastAPI 后端服务的地址
- **用途**：前端通过这个地址与你的后端通信
- **默认值**：`http://localhost:8000`
- **谁运行**：你本地运行的 Python 后端（`python main.py`）

### 2. LLM API 地址 (LLM Base URL)
```
https://api.servicesessentials.ibm.com/v1
```
- **这是什么**：你的 LLM 服务地址（IBM/OpenAI 等）
- **用途**：前端把这个地址传给后端，后端再用它调用 LLM
- **示例**：
  - OpenAI: `https://api.openai.com/v1`
  - IBM: `https://api.servicesessentials.ibm.com/v1`
  - 其他兼容服务：根据你的服务商提供

## 🎯 正确配置步骤

### 步骤 1：启动后端
```bash
cd backend
python main.py
```
后端会在 `http://localhost:8000` 启动

### 步骤 2：启动前端
```bash
npm run dev
```
前端会在 `http://localhost:5173` 启动

### 步骤 3：打开前端并配置

1. 打开浏览器访问 `http://localhost:5173`
2. 点击设置面板（或首次使用会自动弹出）
3. **正确填写**：
   ```
   后端地址: http://localhost:8000
   LLM API 地址: https://api.servicesessentials.ibm.com/v1
   API Key: 你的 IBM API Key
   模型: gpt-4o-mini（或其他支持的模型）
   ```
4. 点击保存

## ❌ 常见错误

### 错误 1：把 LLM API 地址填到后端地址
```
❌ 后端地址: https://api.servicesessentials.ibm.com/v1
```
**结果**：CORS 错误，前端直接访问 LLM API 而不是本地后端

**正确做法**：
```
✅ 后端地址: http://localhost:8000
✅ LLM API 地址: https://api.servicesessentials.ibm.com/v1
```

### 错误 2：后端没有启动
```
❌ 后端地址: http://localhost:8000（但后端没运行）
```
**结果**：NetworkError，无法连接到后端

**正确做法**：先启动后端 `python main.py`

### 错误 3：API Key 未配置
```
❌ API Key: （空）
```
**结果**：LLM API 返回 401 错误

**正确做法**：填入有效的 API Key

## 🔍 验证配置

### 方法 1：查看浏览器控制台
打开浏览器开发者工具（F12），查看 Console：
- 应该看到 `Fetching tools from: http://localhost:8000/api/tools`
- 不应该看到访问 LLM API 地址的请求

### 方法 2：查看 Network 标签
在开发者工具的 Network 标签中：
- 应该看到请求发往 `http://localhost:8000`
- 请求路径应该是 `/api/tools` 和 `/api/chat`

### 方法 3：测试后端
```bash
curl http://localhost:8000/
```
应该返回：
```json
{"status":"ok","service":"Workforce Operations Agent","version":"0.1.0"}
```

## 📊 数据流向

```
用户输入
   ↓
前端 (React)
   ↓ POST /api/chat (带 LLM 配置)
后端 (FastAPI @ localhost:8000)
   ↓ 调用 LLM API (带 API Key)
LLM 服务 (IBM/OpenAI)
   ↓ 返回响应
后端
   ↓ SSE 流式返回
前端
   ↓ 显示结果
用户
```

## 💡 小贴士

1. **后端地址一般不需要改**：除非你把后端部署在其他端口或服务器
2. **LLM API 地址根据你的服务商**：IBM、OpenAI、Azure 等各有不同
3. **API Key 要保密**：不要提交到 git，使用 .env 文件管理
4. **前端配置会覆盖后端 .env**：如果前端填了配置，会优先使用前端配置

## 🆘 还是有问题？

1. 查看后端日志（运行 `python main.py` 的终端）
2. 查看浏览器控制台错误信息
3. 参考 `TROUBLESHOOTING.md` 详细故障排除指南
4. 运行测试脚本：`python backend/test_config.py`
