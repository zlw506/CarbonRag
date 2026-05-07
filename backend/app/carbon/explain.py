from app.carbon.schemas import CarbonBreakdownItem, CarbonCitation, CarbonFactor, CarbonFormulaTrace


class CarbonExplainer:
    def build_formula_summary(self, breakdown: list[CarbonBreakdownItem]) -> str:
        active_items = [item.item for item in breakdown if item.activity_value > 0]
        if not active_items:
            return "排放量 = 活动数据 × 排放因子。当前未提供可计算的活动数据。"
        joined = "、".join(active_items)
        return f"排放量 = 归一化活动数据 × 排放因子；总排放量为 {joined} 分项排放量之和。"

    def build_formula_summary_from_trace(self, traces: list[CarbonFormulaTrace]) -> str:
        if not traces:
            return "排放量 = 活动数据 × 排放因子。当前未提供可计算的活动数据。"
        joined = "、".join(trace.activity_name for trace in traces)
        return f"排放量 = 归一化活动数据 × 排放因子；本次核算包含 {joined}。"

    def build_citations(self, factors: dict[str, CarbonFactor]) -> list[CarbonCitation]:
        ordered_items = ("electricity", "natural_gas", "diesel")
        return [
            CarbonCitation(
                factor_id=factors[item].factor_id,
                source=factors[item].source,
                source_url=factors[item].source_url,
            )
            for item in ordered_items
        ]
