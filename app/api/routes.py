import json
import logging
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models import Chunk, Document, QueryLog
from app.services.llm import call_deepseek_chat
from app.services.retrieval import retriever

logger = logging.getLogger("api")
settings = get_settings()

router = APIRouter()


@router.get("/健康检查", summary="健康检查接口", description="用于检查服务当前是否正常运行。")
async def health_check():
    return {"服务状态": "正常"}


def split_into_chunks(text: str) -> list[str]:
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须为正整数")
    if overlap < 0:
        raise ValueError("overlap 不能为负数")

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        if end >= length:
            break
        start = end - overlap

    return chunks


@router.post("/上传文档", summary="上传文档并切片", description="上传 txt 或 md 文本文件，将其按指定长度切分成分片并写入数据库。")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    db: Session = Depends(get_db),
):
    if tenant_id is None or not tenant_id.strip():
        raise HTTPException(status_code=400, detail="缺少 X-Tenant-Id 请求头")

    if file.content_type not in {"text/plain", "text/markdown"}:
        raise HTTPException(status_code=400, detail="仅支持 txt 或 md 文本文件")

    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码必须为 UTF-8 文本")

    document = Document(
        tenant_id=tenant_id,
        name=file.filename or "未命名文件",
        source_type="upload",
        version=1,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    text_chunks = split_into_chunks(text)
    created = 0
    for idx, chunk_text in enumerate(text_chunks):
        chunk = Chunk(
            document_id=document.id,
            tenant_id=tenant_id,
            chunk_index=idx,
            text=chunk_text,
            metadata_json="{}",
        )
        db.add(chunk)
        created += 1

    db.commit()

    logger.info("文档上传完成 document_id=%s tenant_id=%s chunk_count=%s", document.id, tenant_id, created)
    return {"文档ID": document.id, "分片数量": created}


@router.get("/数据库状态", summary="数据库状态查询", description="返回 documents、chunks、query_logs 三张表的记录数量，可按租户筛选。")
def database_status(
    tenant_id: Optional[str] = Query(default=None, description="可选的租户 ID 过滤条件"),
    db: Session = Depends(get_db),
):
    query_docs = db.query(Document)
    query_chunks = db.query(Chunk)
    query_logs = db.query(QueryLog)

    if tenant_id is not None and tenant_id.strip():
        query_docs = query_docs.filter(Document.tenant_id == tenant_id)
        query_chunks = query_chunks.filter(Chunk.tenant_id == tenant_id)
        query_logs = query_logs.filter(QueryLog.tenant_id == tenant_id)

    return {
        "文档数量": query_docs.count(),
        "分片数量": query_chunks.count(),
        "查询日志数量": query_logs.count(),
    }


@router.post("/检索", summary="仅检索（不调用大模型）", description="用于测试当前租户知识库检索效果，返回命中的分片及分数。")
async def search_only(
    body: dict,
    tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    db: Session = Depends(get_db),
):
    if tenant_id is None or not tenant_id.strip():
        raise HTTPException(status_code=400, detail="缺少 X-Tenant-Id 请求头")

    question = body.get("问题")
    if not question or not isinstance(question, str):
        raise HTTPException(status_code=400, detail="请求体中必须包含 '问题' 字段")

    try:
        top_k = int(body.get("召回数量", settings.top_k_default))
    except (TypeError, ValueError):
        top_k = settings.top_k_default
    if top_k <= 0:
        top_k = settings.top_k_default

    results = retriever.retrieve(db=db, tenant_id=tenant_id, question=question, top_k=top_k)

    return {
        "命中数量": len(results),
        "命中": [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "score": float(score),
                "片段": chunk.text[:300],
            }
            for chunk, score in results
        ],
    }


@router.post("/提问", summary="企业知识库问答", description="对当前租户的知识库进行语义检索并调用大模型生成回答。")
async def ask_question(
    request: Request,
    body: dict,
    tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    db: Session = Depends(get_db),
):
    if tenant_id is None or not tenant_id.strip():
        raise HTTPException(status_code=400, detail="缺少 X-Tenant-Id 请求头")

    question = body.get("问题")
    if not question or not isinstance(question, str):
        raise HTTPException(status_code=400, detail="请求体中必须包含 '问题' 字段")

    try:
        top_k = int(body.get("召回数量", settings.top_k_default))
    except (TypeError, ValueError):
        top_k = settings.top_k_default
    if top_k <= 0:
        top_k = settings.top_k_default

    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start = time.perf_counter()

    results = retriever.retrieve(db=db, tenant_id=tenant_id, question=question, top_k=top_k)
    best_score = results[0][1] if results else 0.0

    refused = False
    reason = ""
    answer_text = ""

    if not results or best_score < settings.similarity_threshold:
        refused = True
        reason = "未检索到足够相关的知识片段，已拒绝回答。"
        answer_text = ""
    else:
        context_text = "\n\n".join(
            f"[文档 {chunk.document_id} - 片段 {chunk.chunk_index}] {chunk.text}"
            for chunk, _score in results
        )
        try:
            answer_text = await call_deepseek_chat(question=question, context=context_text)
        except RuntimeError as exc:
            refused = True
            reason = str(exc)
            answer_text = ""
        except Exception as exc:  # noqa: BLE001
            logger.exception("调用 DeepSeek 失败 request_id=%s tenant_id=%s: %s", request_id, tenant_id, exc)
            refused = True
            reason = "调用大模型服务失败，请稍后重试。"
            answer_text = ""

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    citations = [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "片段": chunk.text,
        }
        for chunk, _score in results
    ]

    response_payload = {
        "回答": answer_text,
        "引用": citations,
        "是否拒答": refused,
        "原因": reason,
    }

    try:
        log = QueryLog(
            request_id=request_id,
            tenant_id=tenant_id,
            question=question,
            topk_chunks_json=json.dumps(
                [
                    {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "score": score,
                    }
                    for chunk, score in results
                ],
                ensure_ascii=False,
            ),
            citations_json=json.dumps(citations, ensure_ascii=False),
            answer_json=json.dumps(response_payload, ensure_ascii=False),
            refused=refused,
            reason=reason,
            latency_ms=elapsed_ms,
        )
        db.add(log)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("写入 query_logs 失败 request_id=%s tenant_id=%s: %s", request_id, tenant_id, exc)

    logger.info(
        "问答完成 request_id=%s tenant_id=%s refused=%s best_score=%.4f latency_ms=%s",
        request_id,
        tenant_id,
        refused,
        best_score,
        elapsed_ms,
    )

    return response_payload