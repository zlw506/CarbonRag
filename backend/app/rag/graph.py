from __future__ import annotations

import re
from typing import Any, Literal, Protocol

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
    entity_name: str | None = None
    relation_type: str | None = None
    reason: str | None = None
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


GraphStoreHealthStatus = Literal["ok", "degraded", "disabled", "error"]


class GraphStoreHealth(BaseModel):
    backend: str
    status: GraphStoreHealthStatus
    available: bool
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphStoreUpsertResult(BaseModel):
    backend: str
    upserted_count: int = 0
    skipped_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphStoreAdapter(Protocol):
    def healthcheck(self) -> GraphStoreHealth:
        ...

    def upsert_entities(self, *, entities: list[GraphEntity]) -> GraphStoreUpsertResult:
        ...

    def upsert_relations(self, *, relations: list[GraphRelation]) -> GraphStoreUpsertResult:
        ...

    def search_entities(self, *, query: str, top_k: int = 5) -> list[GraphEntity]:
        ...

    def search_relations(self, *, query: str, top_k: int = 5) -> list[GraphRelation]:
        ...


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


class RuntimeGraphStoreAdapter:
    backend = "runtime"

    def __init__(self, *, store: InMemoryGraphCandidateStore | None = None) -> None:
        self.store = store or InMemoryGraphCandidateStore()

    def healthcheck(self) -> GraphStoreHealth:
        return GraphStoreHealth(
            backend=self.backend,
            status="ok",
            available=True,
            metadata={
                "adapter_name": type(self).__name__,
                "entity_count": len(self.store.entities_by_id),
                "relation_count": len(self.store.relations_by_id),
                "candidate_count": len(self.store.candidates_by_id),
            },
        )

    def upsert_entities(self, *, entities: list[GraphEntity]) -> GraphStoreUpsertResult:
        self.store.entities_by_id.update({entity.entity_id: entity for entity in entities})
        return GraphStoreUpsertResult(backend=self.backend, upserted_count=len(entities))

    def upsert_relations(self, *, relations: list[GraphRelation]) -> GraphStoreUpsertResult:
        self.store.relations_by_id.update({relation.relation_id: relation for relation in relations})
        return GraphStoreUpsertResult(backend=self.backend, upserted_count=len(relations))

    def search_entities(self, *, query: str, top_k: int = 5) -> list[GraphEntity]:
        query_tokens = set(_tokenize(query))
        scored = [
            (len(query_tokens & set(_tokenize(f"{entity.name} {entity.entity_type}"))) + entity.confidence, entity)
            for entity in self.store.entities_by_id.values()
        ]
        scored = [item for item in scored if item[0] > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entity for _, entity in scored[:top_k]]

    def search_relations(self, *, query: str, top_k: int = 5) -> list[GraphRelation]:
        query_tokens = set(_tokenize(query))
        scored = [
            (
                len(query_tokens & set(_tokenize(f"{relation.relation_type} {relation.description or ''}")))
                + relation.confidence,
                relation,
            )
            for relation in self.store.relations_by_id.values()
        ]
        scored = [item for item in scored if item[0] > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [relation for _, relation in scored[:top_k]]


class FakeGraphStoreAdapter(RuntimeGraphStoreAdapter):
    backend = "fake"

    def __init__(
        self,
        *,
        store: InMemoryGraphCandidateStore | None = None,
        available: bool = True,
        reason: str = "fake_graph_store_unavailable",
    ) -> None:
        super().__init__(store=store)
        self.available = available
        self.reason = reason

    def healthcheck(self) -> GraphStoreHealth:
        if not self.available:
            return GraphStoreHealth(
                backend=self.backend,
                status="degraded",
                available=False,
                reason=self.reason,
                metadata={"adapter_name": type(self).__name__},
            )
        health = super().healthcheck()
        return health.model_copy(update={"backend": self.backend})


class Neo4jGraphStoreAdapter:
    backend = "neo4j"

    def __init__(self, *, reason: str = "neo4j_graph_store_not_configured") -> None:
        self.reason = reason

    def healthcheck(self) -> GraphStoreHealth:
        return GraphStoreHealth(
            backend=self.backend,
            status="disabled",
            available=False,
            reason=self.reason,
            metadata={"adapter_name": type(self).__name__, "optional": True},
        )

    def upsert_entities(self, *, entities: list[GraphEntity]) -> GraphStoreUpsertResult:
        return GraphStoreUpsertResult(
            backend=self.backend,
            skipped_count=len(entities),
            metadata={"reason": self.reason},
        )

    def upsert_relations(self, *, relations: list[GraphRelation]) -> GraphStoreUpsertResult:
        return GraphStoreUpsertResult(
            backend=self.backend,
            skipped_count=len(relations),
            metadata={"reason": self.reason},
        )

    def search_entities(self, *, query: str, top_k: int = 5) -> list[GraphEntity]:
        del query, top_k
        return []

    def search_relations(self, *, query: str, top_k: int = 5) -> list[GraphRelation]:
        del query, top_k
        return []


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


def select_graph_candidates(
    *,
    mode: str,
    question: str,
    build_result: GraphIndexBuildResult,
    top_k: int,
) -> tuple[list[GraphCandidate], str | None]:
    if mode == "off":
        return [], None
    if build_result.status != "ok":
        reason = str(build_result.metadata.get("reason") or build_result.status or "graph_unavailable")
        return [], reason
    if not build_result.candidates:
        return [], "graph_returned_no_candidates"

    if mode == "graph_local":
        selected = _select_local_candidates(question=question, build_result=build_result, top_k=top_k)
        return selected, None if selected else "graph_local_returned_no_candidates"
    if mode == "graph_global":
        selected = _select_global_candidates(question=question, build_result=build_result, top_k=top_k)
        return selected, None if selected else "graph_global_returned_no_candidates"
    if mode == "graph_hybrid":
        local = _select_local_candidates(question=question, build_result=build_result, top_k=top_k)
        global_candidates = _select_global_candidates(question=question, build_result=build_result, top_k=top_k)
        selected = _dedupe_graph_candidates([*local, *global_candidates, *build_result.candidates])[:top_k]
        return selected, None if selected else "graph_hybrid_returned_no_candidates"
    return [], f"unsupported_graph_mode:{mode}"


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


def _select_local_candidates(
    *,
    question: str,
    build_result: GraphIndexBuildResult,
    top_k: int,
) -> list[GraphCandidate]:
    query_tokens = set(_tokenize(question))
    entities_by_id = {entity.entity_id: entity for entity in build_result.entities}
    scored: list[GraphCandidate] = []
    for candidate in build_result.candidates:
        candidate_entities = [entities_by_id[entity_id] for entity_id in candidate.entity_ids if entity_id in entities_by_id]
        entity_text = " ".join(entity.name for entity in candidate_entities)
        overlap = len(query_tokens & set(_tokenize(entity_text)))
        exact_boost = 1 if any(entity.name and entity.name in question for entity in candidate_entities) else 0
        score = candidate.score + float(overlap) + float(exact_boost)
        if score <= 0:
            continue
        primary = candidate_entities[0] if candidate_entities else None
        scored.append(
            candidate.model_copy(
                update={
                    "score": round(score, 6),
                    "entity_name": primary.name if primary else candidate.entity_name,
                    "reason": "graph_local:query_entity_overlap",
                }
            )
        )
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def _select_global_candidates(
    *,
    question: str,
    build_result: GraphIndexBuildResult,
    top_k: int,
) -> list[GraphCandidate]:
    query_tokens = set(_tokenize(question))
    relations_by_id = {relation.relation_id: relation for relation in build_result.relations}
    scored: list[GraphCandidate] = []
    for candidate in build_result.candidates:
        candidate_relations = [
            relations_by_id[relation_id]
            for relation_id in candidate.relation_ids
            if relation_id in relations_by_id
        ]
        if not candidate_relations:
            continue
        relation_text = " ".join(
            f"{relation.relation_type} {relation.description or ''}"
            for relation in candidate_relations
        )
        overlap = len(query_tokens & set(_tokenize(relation_text)))
        score = candidate.score + float(len(candidate_relations)) + float(overlap)
        primary = candidate_relations[0]
        scored.append(
            candidate.model_copy(
                update={
                    "score": round(score, 6),
                    "relation_type": primary.relation_type,
                    "reason": "graph_global:relation_or_community_evidence",
                }
            )
        )
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def _dedupe_graph_candidates(candidates: list[GraphCandidate]) -> list[GraphCandidate]:
    by_key: dict[str, GraphCandidate] = {}
    for candidate in candidates:
        chunk_key = "|".join(candidate.source_chunk_ids)
        key = candidate.candidate_id or chunk_key
        existing = by_key.get(key)
        if existing is None or candidate.score > existing.score:
            by_key[key] = candidate
    return sorted(by_key.values(), key=lambda item: item.score, reverse=True)


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
        primary_relation = chunk_relations[0] if chunk_relations else None
        candidates.append(
            GraphCandidate(
                candidate_id=f"graph-candidate-{hash_content(chunk.chunk_id)[:12]}",
                title=chunk.title,
                snippet=snippet,
                source_chunk_ids=[chunk.chunk_id],
                entity_ids=[entity.entity_id for entity in chunk_entities],
                relation_ids=[relation.relation_id for relation in chunk_relations],
                entity_name=chunk_entities[0].name if chunk_entities else None,
                relation_type=primary_relation.relation_type if primary_relation else None,
                reason="rule_based_chunk_entity_relation",
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
