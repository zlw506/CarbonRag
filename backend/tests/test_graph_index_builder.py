from app.rag.contracts import ChunkRecord
from app.rag.graph import (
    GraphEntity,
    GraphRelation,
    RuleBasedGraphIndexBuilder,
)


def build_chunk(*, chunk_id: str = "policy_001_chunk_01", text: str | None = None) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        document_id=chunk_id.split("_chunk_")[0],
        text=text
        or "2030年前碳达峰行动方案提出完善碳排放统计核算体系，并推动企业开展碳核算。",
        source_type="public_policy",
        title="国务院关于印发2030年前碳达峰行动方案的通知",
        source="test-source",
    )


def test_graph_entity_can_be_created() -> None:
    entity = GraphEntity(
        entity_id="entity-policy-001",
        name="2030年前碳达峰行动方案",
        entity_type="policy",
        source_chunk_ids=["policy_001_chunk_01"],
        confidence=0.9,
    )

    assert entity.name == "2030年前碳达峰行动方案"
    assert entity.confidence == 0.9
    assert entity.source_chunk_ids == ["policy_001_chunk_01"]


def test_graph_relation_can_be_created() -> None:
    relation = GraphRelation(
        relation_id="relation-001",
        source_entity_id="entity-policy-001",
        target_entity_id="entity-term-001",
        relation_type="policy_mentions",
        description="policy mentions term",
        source_chunk_ids=["policy_001_chunk_01"],
        confidence=0.8,
    )

    assert relation.relation_type == "policy_mentions"
    assert relation.weight == 0.8
    assert relation.description == "policy mentions term"


def test_graph_index_builder_build_returns_candidates() -> None:
    builder = RuleBasedGraphIndexBuilder()

    result = builder.build(chunks=[build_chunk()])

    assert result.status == "ok"
    assert result.entity_count >= 2
    assert result.relation_count >= 1
    assert result.candidate_count >= 1
    assert result.candidates[0].source_chunk_ids == ["policy_001_chunk_01"]


def test_graph_index_builder_handles_empty_chunks() -> None:
    builder = RuleBasedGraphIndexBuilder()

    result = builder.build(chunks=[])

    assert result.status == "ok"
    assert result.entities == []
    assert result.relations == []
    assert result.candidates == []


def test_graph_candidates_can_be_looked_up_by_chunk_id() -> None:
    builder = RuleBasedGraphIndexBuilder()
    chunk = build_chunk(chunk_id="enterprise_doc_001_chunk_01", text="华北示例制造厂正在整理月度能耗台账。")

    result = builder.build(chunks=[chunk])
    candidates = builder.candidates_by_chunk_id(chunk_id=chunk.chunk_id)

    assert result.candidates
    assert candidates
    assert candidates[0].source_chunk_ids == [chunk.chunk_id]
