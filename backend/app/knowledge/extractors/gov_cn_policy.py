from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from parsel import Selector


@dataclass(frozen=True)
class ExtractedPolicyDocument:
    title: str | None
    document_no: str | None
    issuer: str | None
    published_date: str | None
    source: str | None
    cleaned_text: str
    markdown: str
    body_char_count: int
    main_selector_used: str
    removed_noise_blocks: int = 0
    extraction_warnings: list[str] = field(default_factory=list)


MAIN_SELECTORS = (
    "#UCAP-CONTENT",
    ".TRS_Editor",
    ".trs_editor",
    ".pages_content",
    ".article",
    ".conTxt",
    ".content",
    "article",
)

MAIN_XPATH_SELECTORS = (
    "//*[@id='UCAP-CONTENT']",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' TRS_Editor ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' trs_editor ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' trs_editor_view ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' pages_content ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' article ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' conTxt ')]",
    "//*[contains(concat(' ', normalize-space(@class), ' '), ' content ')]",
    "//article",
)

NOISE_PATTERNS = (
    "中国政府网",
    "国务院客户端",
    "登录",
    "注册",
    "邮箱",
    "无障碍",
    "长者版",
    "搜索",
    "打印",
    "收藏",
    "分享",
    "责任编辑",
    "网站地图",
    "版权所有",
)


def extract_gov_cn_policy_html(html_text: str, url: str) -> ExtractedPolicyDocument:
    selector = Selector(text=html_text)
    title = _extract_title(selector)
    page_text = "\n".join(selector.xpath("//body//text()").getall())
    published_date = _extract_labeled_value(page_text, "发布日期") or _first_match(
        html_text,
        (
            r"发布时间[:：]\s*([0-9]{4}年[0-9]{2}月[0-9]{2}日)",
            r"firstpublishedtime['\"]?\s+content=['\"]([0-9]{4})-([0-9]{2})-([0-9]{2})",
            r"([0-9]{4}年[0-9]{2}月[0-9]{2}日)",
            r"([0-9]{4}-[0-9]{2}-[0-9]{2})",
        ),
    )
    if published_date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", published_date):
        year, month, day = published_date.split("-")
        published_date = f"{year}年{month}月{day}日"
    source = _extract_source(html_text)
    body_text, selector_used, removed_noise_blocks, warnings = _extract_body(selector, html_text)
    document_no = _first_match(body_text, (r"(国发〔\d{4}〕\d+号)", r"([\u4e00-\u9fa5]{1,8}〔\d{4}〕\d+号)"))
    issuer = _extract_issuer(body_text)
    body_char_count = len(re.sub(r"\s+", "", body_text))
    markdown = _to_markdown(
        title=title,
        url=url,
        document_no=document_no,
        issuer=issuer,
        published_date=published_date,
        source=source,
        body_text=body_text,
    )
    if body_char_count < 800:
        warnings.append("body_too_short")
    return ExtractedPolicyDocument(
        title=title,
        document_no=document_no,
        issuer=issuer,
        published_date=published_date,
        source=source,
        cleaned_text=body_text,
        markdown=markdown,
        body_char_count=body_char_count,
        main_selector_used=selector_used,
        removed_noise_blocks=removed_noise_blocks,
        extraction_warnings=warnings,
    )


def is_gov_cn_policy_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"www.gov.cn", "gov.cn"}


def _extract_title(selector: Selector) -> str | None:
    candidates = []
    candidates.extend(selector.css("h1::text").getall())
    candidates.extend(selector.css("title::text").getall())
    candidates.extend(selector.css("meta[name='ArticleTitle']::attr(content)").getall())
    candidates.extend(selector.css("meta[property='og:title']::attr(content)").getall())
    for item in candidates:
        title = _normalize_line(item)
        if not title:
            continue
        title = re.sub(r"[_\-—].*?(中国政府网|国务院)", "", title).strip()
        if title:
            return title
    return None


def _extract_source(html_text: str) -> str | None:
    patterns = (
        r"来源[:：]\s*([^<\s]{2,30})",
        r"信息来源[:：]\s*([^<\s]{2,30})",
    )
    return _first_match(html.unescape(html_text), patterns)


def _extract_body(selector: Selector, html_text: str) -> tuple[str, str, int, list[str]]:
    warnings: list[str] = []
    best_text = ""
    best_selector = "none"
    removed_noise_blocks = 0
    for css_selector in MAIN_SELECTORS:
        nodes = selector.css(css_selector)
        if not nodes:
            continue
        for node in nodes:
            raw_lines = node.xpath(".//text()").getall()
            cleaned, removed = _clean_lines(raw_lines)
            if len(cleaned) > len(best_text):
                best_text = cleaned
                best_selector = css_selector
                removed_noise_blocks = removed
    for xpath_selector in MAIN_XPATH_SELECTORS:
        nodes = selector.xpath(xpath_selector)
        if not nodes:
            continue
        for node in nodes:
            raw_lines = node.xpath(".//text()").getall()
            cleaned, removed = _clean_lines(raw_lines)
            if len(cleaned) > len(best_text):
                best_text = cleaned
                best_selector = xpath_selector
                removed_noise_blocks = removed
    if not best_text:
        best_text = _anchor_fallback(html_text)
        best_selector = "anchor_fallback"
        warnings.append("main_selector_not_found")
    if not best_text:
        fallback_lines = selector.xpath("//body//text()").getall()
        best_text, removed_noise_blocks = _clean_lines(fallback_lines)
        best_selector = "body_text_fallback"
        warnings.append("body_fallback_used")
    return best_text, best_selector, removed_noise_blocks, warnings


def _anchor_fallback(html_text: str) -> str:
    text = re.sub(r"<(script|style|noscript|svg|canvas)[^>]*>.*?</\1>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"</(p|div|section|article|header|footer|li|tr|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    start_candidates = [
        text.find("国务院关于"),
        text.find("国发〔"),
        text.find("各省、自治区"),
        text.find("一、总体要求"),
    ]
    starts = [item for item in start_candidates if item >= 0]
    if starts:
        text = text[min(starts) :]
    end_candidates = [idx for token in ("责任编辑", "打印", "分享", "网站地图", "版权所有") if (idx := text.find(token)) > 0]
    if end_candidates:
        text = text[: min(end_candidates)]
    cleaned, _removed = _clean_lines(text.splitlines())
    return cleaned


def _clean_lines(raw_lines: list[str]) -> tuple[str, int]:
    lines: list[str] = []
    removed = 0
    for raw in raw_lines:
        line = _normalize_line(raw)
        if not line:
            continue
        if _is_noise_line(line):
            removed += 1
            continue
        lines.append(line)
    return _compact_policy_lines(lines), removed


def _normalize_line(value: str) -> str:
    value = html.unescape(value or "").replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _is_noise_line(line: str) -> bool:
    if len(line) <= 1:
        return True
    if line in NOISE_PATTERNS:
        return True
    if any(line.startswith(token) for token in ("当前位置：", "首页", "字号：", "【字体：", "扫一扫", "客户端")):
        return True
    return False


def _compact_policy_lines(lines: list[str]) -> str:
    compacted: list[str] = []
    for line in lines:
        if compacted and line == compacted[-1]:
            continue
        compacted.append(line)
    return "\n".join(compacted).strip()


def _first_match(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            if match.lastindex and match.lastindex >= 3 and all(match.group(i) for i in (1, 2, 3)):
                return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            return _normalize_line(match.group(1))
    return None


def _extract_labeled_value(text: str, label: str) -> str | None:
    compact = [line for line in (_normalize_line(item) for item in text.splitlines()) if line]
    for index, line in enumerate(compact):
        normalized = re.sub(r"\s+", "", line)
        if normalized.startswith(label):
            inline = re.sub(rf"^\s*{re.escape(label)}\s*[:：]?\s*", "", line)
            if inline and inline != line:
                return inline
            for value in compact[index + 1 : index + 4]:
                if not re.search(r"(索引号|主题分类|发文机关|成文日期|标题|发文字号|发布日期)", value):
                    return value
    return None


def _extract_issuer(body_text: str) -> str | None:
    for line in body_text.splitlines():
        if line in {"国务院", "国务院办公厅"}:
            return line
    return None


def _to_markdown(
    *,
    title: str | None,
    url: str,
    document_no: str | None,
    issuer: str | None,
    published_date: str | None,
    source: str | None,
    body_text: str,
) -> str:
    parts = [f"# {title or '中国政府网政策文件'}", "", f"- URL: {url}"]
    if document_no:
        parts.append(f"- 文号: {document_no}")
    if issuer:
        parts.append(f"- 发布机关: {issuer}")
    if published_date:
        parts.append(f"- 发布日期: {published_date}")
    if source:
        parts.append(f"- 来源: {source}")
    parts.append("")
    parts.append(body_text.strip())
    return "\n".join(parts).strip() + "\n"
