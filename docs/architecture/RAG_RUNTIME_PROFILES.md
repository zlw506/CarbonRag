# RAG Runtime Profiles

CarbonRag V1.6.8 fixes the RAG-Pro runtime split:

- Windows delivery uses Docker Milvus Standalone.
- WSL/Linux/macOS may use Milvus Lite `.db`.
- Memory is development-only fallback.

## Windows Docker Milvus Standalone

Use on native Windows:

```powershell
Copy-Item .env.rag.windows-docker.example .env.rag.local
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/rag-start-milvus-docker-windows.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/rag-smoke-milvus-standalone.ps1
```

Expected runtime trace:

```json
{
  "vector_backend": "milvus",
  "vector_runtime": "milvus_standalone",
  "degraded": false
}
```

`vector_backend` may be configured as `milvus`, but the observable runtime must be `milvus_standalone` when `RAG_MILVUS_URI=http://127.0.0.1:19530`.

## WSL/Linux/macOS Milvus Lite

Use only where `milvus-lite` is supported:

```env
RAG_VECTOR_BACKEND=milvus_lite
RAG_MILVUS_URI=./data/outputs/milvus_lite/carbonrag.db
```

Native Windows should not attempt to install `milvus-lite`.

## Memory Dev Fallback

Use only for fast UI or API development:

```env
RAG_VECTOR_BACKEND=memory
RAG_REQUIRE_REAL_VECTOR=false
```

Any RAG trace from this profile must be degraded and cannot satisfy RAG-Pro acceptance.

## Model Placement

Offline model packages belong here:

```text
data/outputs/models/BAAI/bge-m3
data/outputs/models/BAAI/bge-reranker-v2-m3
```

Do not put models in the source tree or Hugging Face's default C-drive cache. If Docker Desktop stores images on C drive and space is low, move Docker Desktop/WSL data to a larger disk before starting Milvus.

## Docker Data Location On #1 Windows Host

#1 has moved Docker Desktop growth data away from the nearly-full C drive:

```text
F:\AcademicHub\Docker\vm-data
F:\AcademicHub\Docker\wsl\DockerDesktopWSL
```

Other teams should use an equivalent large local disk before pulling Milvus images. Docker program files may stay under `C:\Program Files\Docker`; the large and growing assets are Docker images, containers, volumes, and WSL VHDX files.

## Real RAG-Pro Smoke

After Docker Milvus is healthy and offline model packages are in place, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/rag-pro-real-vector-smoke.ps1
```

The smoke must show all of the following in trace:

```text
dense_count >= 1
sparse_count >= 1
rerank_applied = true
vector_backend = milvus
vector_runtime = milvus_standalone
degraded = false
```
