---
name: report-file-generation
description: Use when CarbonRag chat users ask to generate, export, download, save, or turn the current conversation into a report file such as Word/DOCX or PDF; trigger on Chinese and English intents like 生成报告, 导出报告, 生成文件, 下载报告, 保存为, Word, DOCX, PDF, report file.
---

# Report File Generation

Use this skill when the user wants CarbonRag to create a downloadable report file from the current chat.

## Workflow

1. Detect explicit file-generation intent: generate/export/download/save a report, Word, DOCX, PDF, or "把刚才内容整理成文件".
2. Choose the report type:
   - `carbon_summary`: carbon accounting results or stored carbon calculations.
   - `mixed_analysis`: combined policy and uploaded/private evidence.
   - `policy_summary`: policy-only summary or fallback.
3. Choose export formats:
   - Default to `docx`.
   - Add `pdf` when the user explicitly asks for PDF.
4. Call `report_file_generate`.
5. If the tool returns files, tell the user the report is ready and include filenames/download links.
6. If the tool returns an error, explain what source evidence is missing and what the user should ask next.

## Rules

- Do not claim a file was generated unless `report_file_generate` returns file records.
- Do not invent download links.
- Prefer existing report/export services instead of writing arbitrary files.
- When evidence is insufficient, ask the user to first get a cited answer or carbon calculation in the chat.
