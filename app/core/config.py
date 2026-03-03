import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = "RAG 数据底座服务"

    # 允许在 .env 里配置 DB_PATH（相对/绝对都行）
    db_path: str = os.getenv("DB_PATH", "data/sqlite/app.db")

    @property
    def db_abs_path(self) -> Path:
        # 关键修复：必须用 file 获取当前文件路径，不能写成 file
        project_root = Path(__file__).resolve().parents[2]
        p = Path(self.db_path)
        return p if p.is_absolute() else (project_root / p)

    @property
    def database_url(self) -> str:
        # 用绝对路径生成 sqlite URL，并强制使用 /
        abs_posix = self.db_abs_path.as_posix()
        return f"sqlite:///{abs_posix}"

    # 检索与问答配置
    top_k_default: int = int(os.getenv("TOP_K", "4"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.1"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))

    # DeepSeek 配置
    deepseek_api_key: str | None = os.getenv("DEEPSEEK_API_KEY")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()

    # 工程兜底：启动时确保目录和文件都存在
    s.db_abs_path.parent.mkdir(parents=True, exist_ok=True)
    s.db_abs_path.touch(exist_ok=True)

    return s
  