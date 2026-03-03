from fastapi.testclient import TestClient

from app.main import app
from app.db import SessionLocal
from app.models import Chunk


client = TestClient(app)


def _get_chunk_count() -> int:
    db = SessionLocal()
    try:
        return db.query(Chunk).count()
    finally:
        db.close()


def test_upload_document_increases_chunks_and_returns_positive_count():
    before = _get_chunk_count()

    content = "这是一个用于测试切分功能的文本。" * 100
    files = {
        "file": ("test.txt", content, "text/plain"),
    }
    headers = {"X-Tenant-Id": "test-tenant"}

    response = client.post("/上传文档", files=files, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["分片数量"] > 0

    after = _get_chunk_count()
    assert after > before


def test_upload_document_without_tenant_id_should_return_400():
    content = "缺少租户头时的测试文本。"
    files = {
        "file": ("test.txt", content, "text/plain"),
    }

    response = client.post("/上传文档", files=files)

    assert response.status_code == 400


def test_docs_page_should_return_200():
    response = client.get("/接口文档")
    assert response.status_code == 200
