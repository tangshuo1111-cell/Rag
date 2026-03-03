# FastAPI 中文示例服务工程骨架

本项目是一个最简可运行的 FastAPI 示例工程，接口文档与返回字段均为中文，适合作为入门骨架项目使用。

---

## 一、项目说明

- **框架**：FastAPI
- **接口文档路径**：`/接口文档`
- **健康检查接口**：`GET /健康检查`
- **健康检查返回示例**：

  ```json
  {
    "服务状态": "正常"
  }
  ```

---

## 二、目录结构

- `app/main.py`：FastAPI 应用入口文件
- `requirements.txt`：Python 依赖列表
- `Dockerfile`：构建应用 Docker 镜像的配置
- `docker-compose.yml`：使用 Docker Compose 启动服务的配置
- `README.md`：项目说明与启动步骤（当前文件）

---

## 三、本地运行（使用 Docker）

> 前提：已在本机安装好 **Docker** 和 **Docker Compose**（Docker Desktop 一般已自带）。

1. 打开终端 / PowerShell，进入本项目根目录（包含 `docker-compose.yml` 的目录），例如：

   ```bash
   cd d:\ai\Rag
   ```

2. 执行以下命令构建并启动服务：

   ```bash
   docker compose up --build
   ```

3. 构建完成并看到类似 “Uvicorn running on http://0.0.0.0:8000” 的日志后，说明服务已成功启动。

---

## 四、访问地址

- **健康检查接口**
  - 请求方式：`GET`
  - 地址：`http://localhost:8000/健康检查`
  - 返回示例：

    ```json
    {
      "服务状态": "正常"
    }
    ```

- **Swagger 在线接口文档（带测试功能）**
  - 地址：`http://localhost:8000/接口文档`

---

## 五、停止服务

- 在运行 `docker compose up --build` 的终端中，按下 `Ctrl + C` 即可停止服务。
- 如需同时删除容器，可执行：

  ```bash
  docker compose down
  ```

---

## 六、后续开发建议

- 可以在 `app/main.py` 中继续添加新的接口（路径、summary、description、返回 JSON 字段都可以使用中文）。
- 如需新增第三方库，请在 `requirements.txt` 中添加对应依赖后，重新执行：

  ```bash
  docker compose up --build
  ```

