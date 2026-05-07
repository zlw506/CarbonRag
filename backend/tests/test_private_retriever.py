from app.retrieval.private_retriever import PrivateSampleRetriever


def test_private_sample_retriever_returns_private_hits_for_energy_question() -> None:
    retriever = PrivateSampleRetriever()

    result = retriever.search(
        question="压缩空气系统的能耗问题是什么？",
        top_k=3,
        knowledge_scope="private_sample",
        allowed_doc_ids={"enterprise_doc_002", "energy_bill_sample_001"},
    )

    assert result.total_hits >= 1
    assert result.hits
    assert all(hit.source_type == "private_sample" for hit in result.hits)
    assert all(hit.doc_id in {"enterprise_doc_002", "energy_bill_sample_001"} for hit in result.hits)


def test_private_sample_retriever_can_return_table_chunks() -> None:
    retriever = PrivateSampleRetriever()

    result = retriever.search(
        question="哪一个月份的 electricity_kwh 更高？",
        top_k=2,
        knowledge_scope="private_sample",
        allowed_doc_ids={"energy_bill_sample_001"},
    )

    assert result.total_hits >= 1
    assert result.hits[0].sample_type == "table"
    assert result.hits[0].chunk_id.startswith("energy_bill_sample_001")


def test_private_sample_retriever_without_explicit_allowed_ids_fails_closed() -> None:
    retriever = PrivateSampleRetriever()

    result = retriever.search(
        question="鍘嬬缉绌烘皵绯荤粺鐨勮兘鑰楅棶棰樻槸浠€涔堬紵",
        top_k=3,
        knowledge_scope="private_sample",
    )

    assert result.total_hits == 0
    assert result.hits == []


def test_private_sample_retriever_empty_allowed_ids_returns_no_hits() -> None:
    retriever = PrivateSampleRetriever()

    result = retriever.search(
        question="鍘嬬缉绌烘皵绯荤粺鐨勮兘鑰楅棶棰樻槸浠€涔堬紵",
        top_k=3,
        knowledge_scope="private_sample",
        allowed_doc_ids=set(),
    )

    assert result.total_hits == 0
    assert result.hits == []
