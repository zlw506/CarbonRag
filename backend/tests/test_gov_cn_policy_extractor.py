from __future__ import annotations

from pathlib import Path

import pytest

from app.knowledge.extractors.gov_cn_policy import extract_gov_cn_policy_html
from app.knowledge.policy_ingestion import CrawledDocument, FakeCrawlerProvider
from app.knowledge.policy_live_crawler import PolicyCrawlerScheduler, PolicyCrawlerStore
from app.core.config import Settings


FIXTURE = Path(__file__).parent / "fixtures" / "crawler" / "gov_cn_service_quality_202604.html"


def test_gov_cn_policy_extractor_extracts_title_docno_date_body() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    extracted = extract_gov_cn_policy_html(html, "https://www.gov.cn/zhengce/content/202604/content_7066483.htm")

    assert extracted.title == "国务院关于推进服务业扩能提质的意见"
    assert extracted.document_no == "国发〔2026〕7号"
    assert extracted.published_date == "2026年04月21日"
    assert "为推进服务业扩能提质，促进服务业优质高效发展" in extracted.cleaned_text
    assert extracted.body_char_count > 2000
    assert extracted.markdown.strip()


def test_gov_cn_policy_extractor_removes_navigation_noise() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    extracted = extract_gov_cn_policy_html(html, "https://www.gov.cn/zhengce/content/202604/content_7066483.htm")

    assert "登录 注册 邮箱" not in extracted.cleaned_text
    assert "责任编辑" not in extracted.cleaned_text
    assert "打印 分享 网站地图" not in extracted.cleaned_text


def test_candidate_artifacts_non_empty_for_gov_cn_fixture(tmp_path) -> None:
    scheduler = _scheduler_with_document(tmp_path, FIXTURE.read_text(encoding="utf-8"))

    run = scheduler.run_source_now(source_id="gov-cn-policy-library", triggered_by_user_id=None)
    candidate = scheduler.list_candidates()[0]

    assert run.status == "succeeded"
    assert candidate.metadata["extraction_quality_score"] >= 60
    assert candidate.metadata["topic_class"] == "indirect_low_carbon_related"
    assert candidate.metadata["markdown_size"] >= 800
    assert candidate.metadata["cleaned_size"] >= 800
    assert candidate.metadata["estimated_chunk_count"] > 0
    assert "国发〔2026〕7号" in Path(candidate.metadata["markdown_storage_path"]).read_text(encoding="utf-8")


def test_candidate_quality_rejects_empty_markdown(tmp_path) -> None:
    html = "<html><body><h1>碳达峰短文</h1><p>碳达峰。</p></body></html>"
    scheduler = _scheduler_with_document(tmp_path, html, title="碳达峰短文")

    scheduler.run_source_now(source_id="gov-cn-policy-library", triggered_by_user_id=None)
    candidate = scheduler.list_candidates()[0]

    assert candidate.metadata["candidate_quality_score"] <= 40
    assert "extract_empty_text" in candidate.metadata["artifact_errors"]


def test_duplicate_candidate_does_not_show_as_normal_pending_publish(tmp_path) -> None:
    scheduler = _scheduler_with_document(tmp_path, FIXTURE.read_text(encoding="utf-8"))

    scheduler.run_source_now(source_id="gov-cn-policy-library", triggered_by_user_id=None)
    scheduler.run_source_now(source_id="gov-cn-policy-library", triggered_by_user_id=None)
    candidate = scheduler.list_candidates()[0]

    assert candidate.metadata["change_type"] == "unchanged"
    assert candidate.metadata["skip_reason"] == "duplicate_content_hash"


def _scheduler_with_document(tmp_path, html: str, *, title: str = "国务院关于推进服务业扩能提质的意见") -> PolicyCrawlerScheduler:
    document = CrawledDocument(
        url="https://www.gov.cn/zhengce/content/202604/content_7066483.htm",
        title=title,
        content=html,
        content_type="text/html",
        source_name="中国政府网",
    )
    store = PolicyCrawlerStore(sqlite_db_path=tmp_path / "carbonrag.sqlite3")
    store.seed_default_sources()
    return PolicyCrawlerScheduler(
        store=store,
        provider=FakeCrawlerProvider(documents=[document]),
        settings=Settings(
            public_data_dir=str(tmp_path / "public"),
            rag_policy_live_crawler_scheduled_enabled=False,
            rag_policy_live_crawler_auto_publish=False,
        ),
        candidate_dir=tmp_path / "public" / "policy_crawl_candidates",
    )


def test_gov_cn_live_smoke_extracts_body_when_network_available() -> None:
    pytest.importorskip("httpx")
    import httpx

    url = "https://www.gov.cn/zhengce/content/202604/content_7066483.htm"
    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"gov.cn live smoke unavailable: {exc}")
    extracted = extract_gov_cn_policy_html(response.text, url)

    assert extracted.title == "国务院关于推进服务业扩能提质的意见"
    assert "国发〔2026〕7号" in extracted.cleaned_text
    assert extracted.body_char_count > 2000
