$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repo "backend"
$python = Join-Path $backend ".conda\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}
Push-Location $backend
$env:PYTHONPATH = "."
$script = @'
import httpx
from app.knowledge.extractors.gov_cn_policy import extract_gov_cn_policy_html

url = "https://www.gov.cn/zhengce/content/202604/content_7066483.htm"
response = httpx.get(url, timeout=30.0)
response.raise_for_status()
extracted = extract_gov_cn_policy_html(response.text, url)
print("fetch_ok", True)
print("extract_ok", extracted.body_char_count > 2000)
print("title", extracted.title)
print("document_no", extracted.document_no)
print("published_date", extracted.published_date)
print("cleaned_size", len(extracted.cleaned_text.encode("utf-8")))
print("markdown_size", len(extracted.markdown.encode("utf-8")))
print("estimated_chunk_count", max(1, (len(extracted.cleaned_text) + 899) // 900))
print("search_query", "服务业 扩能提质 节能环保服务")
'@
$script | & $python -
Pop-Location
