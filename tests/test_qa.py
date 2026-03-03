from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ask_question_after_upload_should_return_answer_or_refusal():
    # 先上传一个文档
    content = "企业知识库 RAG 系统用于支持员工快速检索公司内部文档信息。"
    files = {
        "file": ("kb.txt", content, "text/plain"),
    }
    headers = {"X-Tenant-Id": "qa-tenant"}

    upload_resp = client.post("/上传文档", files=files, headers=headers)
    assert upload_resp.status_code == 200

    # 再发起提问
    question_body = {
        "问题": "这个系统是用来做什么的？",
        "召回数量": 4,
    }
    qa_resp = client.post("/提问", json=question_body, headers=headers)

    assert qa_resp.status_code == 200
    data = qa_resp.json()
    assert "回答" in data
    assert "是否拒答" in data


def test_ask_question_without_tenant_id_should_return_400():
    question_body = {
        "问题": "没有租户信息的提问会怎样？",
    }

    resp = client.post("/提问", json=question_body)
    assert resp.status_code == 400

