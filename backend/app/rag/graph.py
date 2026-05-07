from __future__ import annotations

import re
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.rag.contracts import ChunkRecord, hash_content


class GraphEntity(BaseModel):
    entity_id: str
    name: str
    entity_type: str = "unknown"
    source_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphRelation(BaseModel):
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str = "related_to"
    description: str | None = None
    source_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def weight(self) -> float:
        return self.confidence


class GraphCommunitySummary(BaseModel):
    community_id: str
    entity_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)
    summary: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    title: str | None = None


class GraphCandidate(BaseModel):
    candidate_id: str
    title: str
    snippet: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphIndexBuildResult(BaseModel):
    status: str
    entities: list[GraphEntity] = Field(default_factory=list)
    relations: list[GraphRelation] = Field(default_factory=list)
    communities: list[GraphCommunitySummary] = Field(default_factory=list)
    candidates: list[GraphCandidate] = Field(default_factory=list)
    entity_count: int = 0
    relation_count: int = 0
    community_count: int = 0
    candidate_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.entity_count == 0 and self.entities:
            self.entity_count = len(self.entities)
        if self.relation_count == 0 and self.relations:
            self.relation_count = len(self.relations)
        if self.community_count == 0 and self.communities:
            self.community_count = len(self.communities)
        if self.candidate_count == 0 and self.candidates:
            self.candidate_count = len(self.candidates)


class GraphIndexBuilder(Protocol):
    def is_available(self) -> bool:
        ...

    def extract_entities(self, *, chunks: list[ChunkRecord]) -> list[GraphEntity]:
        ...

    def extract_relations(self, *, chunks: list[ChunkRecord], entities: list[GraphEntity]) -> list[GraphRelation]:
        ...

    def build_summary(
        self,
        *,
        entities: list[GraphEntity],
        relations: list[GraphRelation],
    ) -> GraphCommunitySummary | None:
        ...

    def build(self, *, chunks: list[ChunkRecord]) -> GraphIndexBuildResult:
        ...

    def search_candidates(self, *, question: str, top_k: int) -> list[GraphCandidate]:
        ...

    def candidates_by_chunk_id(self, *, chunk_id: str) -> list[GraphCandidate]:
        ...


class InMemoryGraphCandidateStore:
    def __init__(self) -> None:
        self.entities_by_id: dict[str, GraphEntity] = {}
        self.relations_by_id: dict[str, GraphRelation] = {}
        self.communities_by_id: dict[str, GraphCommunitySummary] = {}
        self.candidates_by_id: dict[str, GraphCandidate] = {}
        self.candidate_ids_by_chunk_id: dict[str, list[str]] = {}

    def save(self, result: GraphIndexBuildResult) -> None:
        self.entities_by_id.update({entity.entity_id: entity for entity in result.entities})
        self.relations_by_id.update({relation.relation_id: relation for relation in result.relations})
        self.communities_by_id.update({community.community_id: community for community in result.communities})
        for candidate in result.candidates:
            self.candidates_by_id[candidate.candidate_id] = candidate
            for chunk_id in candidate.source_chunk_ids:
                existing = self.candidate_ids_by_chunk_id.setdefault(chunk_id, [])
                if candidate.candidate_id not in existing:
                    existing.append(candidate.candidate_id)

    def by_chunk_id(self, *, chunk_id: str) -> list[GraphCandidate]:
        return [
            self.candidates_by_id[candidate_id]
            for candidate_id in self.candidate_ids_by_chunk_id.get(chunk_id, [])
            if candidate_id in self.candidates_by_id
        ]

    def search(self, *, question: str, top_k: int) -> list[GraphCandidate]:
        query_tokens = set(_tokenize(question))
        scored: list[GraphCandidate] = []
        for candidate in self.candidates_by_id.values():
            candidate_tokens = set(_tokenize(f"{candidate.title} {candidate.snippet}"))
            overlap = len(query_tokens & candidate_tokens)
            score = candidate.score + float(overlap)
            if score <= 0:
                continue
            scored.append(candidate.model_copy(update={"score": round(score, 6)}))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


class RuleBasedGraphIndexBuilder:
    def __init__(self, *, store: InMemoryGraphCandidateStore | None = None) -> None:
        self.store = store or InMemoryGraphCandidateStore()

    def is_available(self) -> bool:
        return True

    def extract_entities(self, *, chunks: list[ChunkRecord]) -> list[GraphEntity]:
        entities_by_id: dict[str, GraphEntity] = {}
        for chunk in chunks:
            for name, entity_type, confidence in _extract_entity_candidates(chunk):
                entity_id = _entity_id(name=name, entity_type=entity_type)
                existing = entities_by_id.get(entity_id)
                if existing is None:
                    entities_by_id[entity_id] = GraphEntity(
                        entity_id=entity_id,
                        name=name,
                        entity_type=entity_type,
                        source_chunk_ids=[chunk.chunk_id],
                        confidence=confidence,
                        metadata={
                            "document_id": chunk.document_id,
                            "source_type": chunk.source_type,
                            "extractor": "rule_based",
                        },
                    )
                    continue
                if chunk.chunk_id not in existing.source_chunk_ids:
                    existing.source_chunk_ids.append(chunk.chunk_id)
                existing.confidence = max(existing.confidence, confidence)
        return list(entities_by_id.values())

    def extract_relations(self, *, chunks: list[ChunkRecord], entities: list[GraphEntity]) -> list[GraphRelation]:
        entities_by_chunk_id: dict[str, list[GraphEntity]] = {}
        for entity in entities:
            for chunk_id in entity.source_chunk_ids:
                entities_by_chunk_id.setdefault(chunk_id, []).append(entity)

        relations_by_id: dict[str, GraphRelation] = {}
        for chunk in chunks:
            chunk_entities = entities_by_chunk_id.get(chunk.chunk_id, [])
            for index, source in enumerate(chunk_entities):
                for target in chunk_entities[index + 1:]:
                    relation_type = _relation_type(source=source, target=target)
                    relation_id = _relation_id(source.entity_id, target.entity_id, relation_type)
                    existing = relations_by_id.get(relation_id)
                    if existing is None:
                        relations_by_id[relation_id] = GraphRelation(
                            relation_id=relation_id,
                            source_entity_id=source.entity_id,
                            target_entity_id=target.entity_id,
                            relation_type=relation_type,
                            description=f"{source.name} 与 {target.name} 在同一证据片段中共同出现。",
                            source_chunk_ids=[chunk.chunk_id],
                            confidence=round(min(source.confidence, target.confidence), 3),
                            metadata={
                                "document_id": chunk.document_id,
                                "extractor": "co_occurrence",
                            },
                        )
                        continue
                    if chunk.chunk_id not in existing.source_chunk_ids:
                        existing.source_chunk_ids.append(chunk.chunk_id)
        return list(relations_by_id.values())

    def build_summary(
        self,
        *,
        entities: list[GraphEntity],
        relations: list[GraphRelation],
    ) -> GraphCommunitySummary | None:
        if not entities and not relations:
            return None
        source_chunk_ids = sorted(
            {
                chunk_id
                for item in [*entities, *relations]
                for chunk_id in item.source_chunk_ids
            }
        )
        entity_names = "、".join(entity.name for entity in entities[:5])
        summary = f"规则图谱候选包含 {len(entities)} 个实体、{len(relations)} 条关系。"
        if entity_names:
            summary = f"{summary} 主要实体：{entity_names}。"
        return GraphCommunitySummary(
            community_id=f"community-{hash_content('|'.join(entity.entity_id for entity in entities))[:12]}",
            entity_ids=[entity.entity_id for entity in entities],
            relation_ids=[relation.relation_id for relation in relations],
            summary=summary,
            source_chunk_ids=source_chunk_ids,
            metadata={"extractor": "rule_based"},
            title="规则抽取图谱摘要",
        )

    def build(self, *, chunks: list[ChunkRecord]) -> GraphIndexBuildResult:
        if not chunks:
            return GraphIndexBuildResult(
                status="ok",
                metadata={"chunk_count": 0, "extractor": "rule_based"},
            )
        entities = self.extract_entities(chunks=chunks)
        relations = self.extract_relations(chunks=chunks, entities=entities)
        summary = self.build_summary(entities=entities, relations=relations)
        candidates = _build_candidates(chunks=chunks, entities=entities, relations=relations, summary=summary)
        result = GraphIndexBuildResult(
            status="ok",
            entities=entities,
            relations=relations,
            communities=[summary] if summary else [],
            candidates=candidates,
            metadata={
                "chunk_count": len(chunks),
                "extractor": "rule_based",
                "storage": "in_memory",
            },
        )
        self.store.save(result)
        return result

    def search_candidates(self, *, question: str, top_k: int) -> list[GraphCandidate]:
        return self.store.search(question=question, top_k=top_k)

    def candidates_by_chunk_id(self, *, chunk_id: str) -> list[GraphCandidate]:
        return self.store.by_chunk_id(chunk_id=chunk_id)


class DisabledGraphIndexBuilder:
    def __init__(self, *, reason: str = "graph_index_unavailable") -> None:
        self.reason = reason

    def is_available(self) -> bool:
        return False

    def extract_entities(self, *, chunks: list[ChunkRecord]) -> list[GraphEntity]:
        del chunks
        return []

    def extract_relations(self, *, chunks: list[ChunkRecord], entities: list[GraphEntity]) -> list[GraphRelation]:
        del chunks, entities
        return []

    def build_summary(
        self,
        *,
        entities: list[GraphEntity],
        relations: list[GraphRelation],
    ) -> GraphCommunitySummary | None:
        del entities, relations
        return None

    def build(self, *, chunks: list[ChunkRecord]) -> GraphIndexBuildResult:
        return GraphIndexBuildResult(
            status="disabled",
            metadata={"reason": self.reason, "chunk_count": len(chunks)},
        )

    def search_candidates(self, *, question: str, top_k: int) -> list[GraphCandidate]:
        del question, top_k
        return []

    def candidates_by_chunk_id(self, *, chunk_id: str) -> list[GraphCandidate]:
        del chunk_id
        return []


def _extract_entity_candidates(chunk: ChunkRecord) -> list[tuple[str, str, float]]:
    text = f"{chunk.title}\n{chunk.text}"
    candidates: list[tuple[str, str, float]] = []

    for name, entity_type, confidence in _KNOWN_TERMS:
        if name in text:
            candidates.append((name, entity_type, confidence))

    for match in re.finditer(r"([\u4e00-\u9fffA-Za-z0-9]{2,30}(?:方案|通知|行动方案|实施方案|体系|标准|台账))", text):
        candidates.append((match.group(1), "policy_or_standard", 0.66))

    if chunk.source_type in {"private_sample", "private_upload"}:
        for match in re.finditer(r"([\u4e00-\u9fff]{2,20}(?:企业|公司|制造厂|工厂))", text):
            candidates.append((match.group(1), "enterprise", 0.72))

    region = chunk.metadata.get("region")
    if isinstance(region, str) and region:
        candidates.append((region, "region", 0.6))
    return _dedupe_candidates(candidates)


def _build_candidates(
    *,
    chunks: list[ChunkRecord],
    entities: list[GraphEntity],
    relations: list[GraphRelation],
    summary: GraphCommunitySummary | None,
) -> list[GraphCandidate]:
    entities_by_chunk_id: dict[str, list[GraphEntity]] = {}
    relations_by_chunk_id: dict[str, list[GraphRelation]] = {}
    for entity in entities:
        for chunk_id in entity.source_chunk_ids:
            entities_by_chunk_id.setdefault(chunk_id, []).append(entity)
    for relation in relations:
        for chunk_id in relation.source_chunk_ids:
            relations_by_chunk_id.setdefault(chunk_id, []).append(relation)

    candidates: list[GraphCandidate] = []
    for chunk in chunks:
        chunk_entities = entities_by_chunk_id.get(chunk.chunk_id, [])
        chunk_relations = relations_by_chunk_id.get(chunk.chunk_id, [])
        if not chunk_entities and not chunk_relations:
            continue
        entity_names = "、".join(entity.name for entity in chunk_entities[:5])
        snippet = entity_names or chunk.text[:120]
        candidates.append(
            GraphCandidate(
                candidate_id=f"graph-candidate-{hash_content(chunk.chunk_id)[:12]}",
                title=chunk.title,
                snippet=snippet,
                source_chunk_ids=[chunk.chunk_id],
                entity_ids=[entity.entity_id for entity in chunk_entities],
                relation_ids=[relation.relation_id for relation in chunk_relations],
                score=round(sum(entity.confidence for entity in chunk_entities), 3),
                metadata={
                    "document_id": chunk.document_id,
                    "source_type": chunk.source_type,
                    "community_id": summary.community_id if summary else None,
                },
            )
        )
    return candidates


def _relation_type(*, source: GraphEntity, target: GraphEntity) -> str:
    if "policy" in {source.entity_type, target.entity_type}:
        return "policy_mentions"
    if "enterprise" in {source.entity_type, target.entity_type}:
        return "enterprise_mentions"
    if "carbon_accounting_term" in {source.entity_type, target.entity_type}:
        return "carbon_accounting_related"
    return "co_occurs"


def _entity_id(*, name: str, entity_type: str) -> str:
    return f"entity-{entity_type}-{hash_content(name)[:12]}"


def _relation_id(source_entity_id: str, target_entity_id: str, relation_type: str) -> str:
    ordered = sorted([source_entity_id, target_entity_id])
    return f"relation-{relation_type}-{hash_content('|'.join([*ordered, relation_type]))[:12]}"


def _dedupe_candidates(candidates: list[tuple[str, str, float]]) -> list[tuple[str, str, float]]:
    by_key: dict[tuple[str, str], float] = {}
    for name, entity_type, confidence in candidates:
        normalized = name.strip()
        if not normalized:
            continue
        key = (normalized, entity_type)
        by_key[key] = max(by_key.get(key, 0.0), confidence)
    return [(name, entity_type, confidence) for (name, entity_type), confidence in by_key.items()]


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"\W+", text.lower())
        if token
    ] + re.findall(r"[\u4e00-\u9fff]{2,}", text)


_KNOWN_TERMS: tuple[tuple[str, str, float], ...] = (
    ("2030年前碳达峰行动方案", "policy", 0.92),
    ("北京市碳达峰实施方案", "policy", 0.9),
    ("碳排放统计核算体系", "carbon_accounting_term", 0.88),
    ("标准计量体系", "standard", 0.84),
    ("产品碳足迹", "carbon_accounting_term", 0.82),
    ("碳核算", "carbon_accounting_term", 0.8),
    ("碳达峰", "carbon_accounting_term", 0.76),
    ("碳中和", "carbon_accounting_term", 0.76),
    ("北京", "region", 0.74),
    ("华北示例制造厂", "enterprise", 0.82),
    ("压缩空气", "carbon_accounting_term", 0.68),
    ("蒸汽系统", "carbon_accounting_term", 0.68),
    ("月度能耗台账", "carbon_accounting_term", 0.7),
    ("运输里程", "carbon_accounting_term", 0.68),
)
