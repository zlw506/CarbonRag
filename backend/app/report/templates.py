from dataclasses import dataclass

from app.report.schemas import ReportType


@dataclass(frozen=True)
class ReportTemplate:
    report_type: ReportType
    display_name: str
    sections: tuple[str, ...]
    purpose: str


TEMPLATES: dict[ReportType, ReportTemplate] = {
    "policy_summary": ReportTemplate(
        report_type="policy_summary",
        display_name="政策解读摘要",
        sections=(
            "问题背景",
            "关键政策依据摘要",
            "结论与建议",
        ),
        purpose="Summarize a policy-grounded conversation into a concise briefing.",
    ),
    "mixed_analysis": ReportTemplate(
        report_type="mixed_analysis",
        display_name="政策与企业样例初步分析",
        sections=(
            "当前问题",
            "相关政策依据",
            "当前企业样例情况",
            "差距与风险",
            "初步建议",
        ),
        purpose="Layer public policy evidence and private sample observations into a mixed analysis.",
    ),
    "carbon_summary": ReportTemplate(
        report_type="carbon_summary",
        display_name="碳核算结果说明",
        sections=(
            "核算周期",
            "活动数据摘要",
            "排放因子与公式",
            "总量与分项",
            "结果说明",
        ),
        purpose="Explain one carbon calculation result in report form.",
    ),
}


def get_report_template(report_type: ReportType) -> ReportTemplate:
    return TEMPLATES[report_type]
