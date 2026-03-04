RAG 


一个基于 FastAPI + SQLite + DeepSeek API 的轻量级企业知识库问答系统，实现文档上传、文本切片、检索增强生成和大模型问答接口。

项目实现了从 文档入库 → 文本切片 → 检索 → LLM 生成回答 → 日志记录 的完整流程，并完成 Docker 容器化与 GHCR 镜像发布。

--

项目背景


在企业内部知识库场景中，员工常常需要快速查询文档信息。传统搜索系统难以理解自然语言问题，因此本项目实现了一个 RAG知识库问答系统。

系统通过检索相关文档片段并结合大模型生成回答，实现更加准确的企业知识问答。


FastAPI SQLAlchemy SQLite TF-IDF Retrieval DeepSeek API Docker GitHub Container Registry





用户提问 FastAPI API 接口 TF-IDF 检索 TopK 文本片段 拼接上下文 Context DeepSeek LLM 生成回答 返回回答 + 引用片段








核心功能


1 文档上传


支持上传 TXT / Markdown 文档。

系统自动：
- 解析文本
- 按长度进行切片
- 写入数据库


---

2 文本切片


采用 chunk_size + overlap 的方式切分文本。

chunk_size = 800
chunk_overlap = 120
避免长文本截断带来的语义损失。



3 检索模块


实现轻量级 TF-IDF 检索算法：
- 对所有文本分片建立 TF-IDF 向量
- 对用户问题进行向量化
- 计算相似度
- 返回 TopK 相关文本片段


---

4 LLM 问答


调用 DeepSeek Chat API：
- 拼接检索到的文本作为 Context
- 生成回答
- 返回引用片段



5 拒答机制

为降低大模型幻觉风险，系统引入 相似度阈值控制：

SIMILARITY_THRESHOLD
当检索相关度不足时：拒绝回答




6 查询日志


系统记录每次问答日志：
- request_id
- tenant_id
- question
- 检索片段
- 生成回答
- 响应时间


用于系统调试与审计。


运行项目


pip install -r requirements.txt
uvicorn app.main:app --reload
http://127.0.0.1:8000/接口文档


API 示例


提问接口：
POST /提问

请求示例：
{
  "问题": "候选人做过哪些项目？",
  "召回数量": 4
}

请求头：
X-Tenant-Id: 123


Docker 运行

docker build -t rag .
docker run -p 8000:8000 rag


镜像仓库


Docker 镜像发布在 GitHub Container Registry：
ghcr.io/tangshuo1111-cell/rag



项目开发说明


项目开发过程中使用 Cursor 进行 AI 辅助编程，用于生成基础代码结构。

在工程实现过程中通过人工调试学习解决了多个问题，包括：
- SQLite 数据库路径问题
- SQLAlchemy ORM 映射问题
- FastAPI 请求体结构错误
- Docker 构建与网络问题
- DeepSeek API 鉴权问题

最终完成了可运行的 RAG API 服务与 Docker 镜像发布流程。
GitHub


代码仓库

https://github.com/tangshuo1111-cell/Rag

Docker 镜像

https://github.com/users/tangshuo1111-cell/packages/container/package/rag
  ```

