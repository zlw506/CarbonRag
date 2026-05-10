from __future__ import annotations

import platform
from dataclasses import dataclass, field

from app.core.config import get_settings


@dataclass(slots=True)
class VectorRuntimeProfile:
    vector_backend: str
    vector_runtime: str
    milvus_uri: str | None = None
    require_real_vector: bool = True
    degraded: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def uses_milvus(self) -> bool:
        return self.vector_backend in {"milvus", "milvus_lite"}

    @property
    def uses_real_vector(self) -> bool:
        return self.vector_runtime in {"milvus_standalone", "milvus_lite"}


def resolve_vector_runtime(*, backend: str | None = None, milvus_uri: str | None = None) -> VectorRuntimeProfile:
    settings = get_settings()
    raw_backend = (backend if backend is not None else settings.rag_vector_backend) or "memory"
    normalized = str(raw_backend).strip().lower().replace("-", "_")
    uri = milvus_uri if milvus_uri is not None else getattr(settings, "rag_milvus_uri", "./data/outputs/milvus_lite/carbonrag.db")
    require_real = bool(getattr(settings, "rag_require_real_vector", True))
    warnings: list[str] = []

    if normalized in {"milvus", "milvus_standalone"}:
        if _is_remote_milvus_uri(uri):
            return VectorRuntimeProfile(
                vector_backend="milvus",
                vector_runtime="milvus_standalone",
                milvus_uri=uri,
                require_real_vector=require_real,
            )
        runtime = "milvus_lite"
        if platform.system().lower() == "windows":
            warnings.append("native Windows does not support milvus-lite; use Docker Milvus Standalone at http://127.0.0.1:19530.")
        return VectorRuntimeProfile(
            vector_backend="milvus_lite",
            vector_runtime=runtime,
            milvus_uri=uri,
            require_real_vector=require_real,
            degraded=bool(warnings),
            warnings=warnings,
        )

    if normalized in {"milvus_lite", "milvuslite"}:
        if platform.system().lower() == "windows":
            warnings.append("native Windows does not support milvus-lite; this profile is only for WSL/Linux/macOS.")
        return VectorRuntimeProfile(
            vector_backend="milvus_lite",
            vector_runtime="milvus_lite",
            milvus_uri=uri,
            require_real_vector=require_real,
            degraded=bool(warnings),
            warnings=warnings,
        )

    if normalized == "chroma":
        return VectorRuntimeProfile(
            vector_backend="chroma",
            vector_runtime="chroma_dev",
            require_real_vector=require_real,
            degraded=True,
            warnings=["Chroma is a compatibility backend; V1.6.8 Windows acceptance requires Docker Milvus Standalone."],
        )

    return VectorRuntimeProfile(
        vector_backend="memory",
        vector_runtime="memory_dev",
        require_real_vector=require_real,
        degraded=True,
        warnings=["memory backend is development-only and cannot satisfy RAG-Pro vector acceptance."],
    )


def is_milvus_backend(backend: str | None) -> bool:
    return resolve_vector_runtime(backend=backend).uses_milvus


def _is_remote_milvus_uri(uri: str | None) -> bool:
    value = (uri or "").strip().lower()
    return value.startswith(("http://", "https://", "tcp://", "grpc://"))
