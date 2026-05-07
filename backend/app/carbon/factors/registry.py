from dataclasses import dataclass

from app.carbon.schemas import CarbonActivityItem
from app.carbon.factors.schema import FactorRecord


@dataclass(frozen=True)
class FactorSelection:
    factor: FactorRecord
    warnings: list[str]


class FactorRegistry:
    def __init__(self, records: list[FactorRecord]) -> None:
        self.records = [record for record in records if not record.is_deprecated]

    def select_factor(self, activity: CarbonActivityItem) -> FactorSelection:
        candidates = [
            record
            for record in self.records
            if record.scope == activity.scope
            and record.activity_category == activity.activity_category
            and record.activity_name == activity.activity_name
        ]
        if not candidates:
            raise ValueError(
                "No carbon factor found for "
                f"{activity.scope}/{activity.activity_category}/{activity.activity_name}."
            )

        warnings: list[str] = []
        preferred = self._filter_by_source_preference(candidates, activity.factor_preference)
        if not preferred:
            preferred = candidates
            warnings.append(
                f"未找到 {activity.activity_name} 的官方因子，已回退到可用演示/备用因子。"
            )

        selected = sorted(
            preferred,
            key=lambda record: (
                self._region_score(record, activity.region),
                self._year_score(record, activity.year),
                int(record.is_default),
            ),
            reverse=True,
        )[0]

        if selected.source_type == "demo":
            warnings.append(
                f"{selected.factor_id} 是 demo 因子，仅用于链路验证，不用于正式盘查或审计。"
            )
        if activity.region and selected.region not in {activity.region, "CN", None}:
            warnings.append(
                f"{activity.activity_name} 未命中请求地区 {activity.region}，使用 {selected.region or 'global'} 因子。"
            )
        if activity.year and selected.year and selected.year != activity.year:
            warnings.append(
                f"{activity.activity_name} 未命中请求年份 {activity.year}，使用 {selected.year} 因子。"
            )

        return FactorSelection(factor=selected, warnings=warnings)

    @staticmethod
    def _filter_by_source_preference(
        candidates: list[FactorRecord],
        preference: str | None,
    ) -> list[FactorRecord]:
        if preference == "official_latest":
            return [record for record in candidates if record.source_type == "official"]
        if preference == "demo_allowed":
            return candidates
        if preference == "any_latest":
            return candidates
        return [record for record in candidates if record.source_type == "official"] or candidates

    @staticmethod
    def _region_score(record: FactorRecord, requested_region: str | None) -> int:
        if requested_region and record.region == requested_region:
            return 3
        if record.region == "CN":
            return 2
        if record.region is None:
            return 1
        return 0

    @staticmethod
    def _year_score(record: FactorRecord, requested_year: int | None) -> int:
        if requested_year is None:
            return record.year or 0
        if record.year == requested_year:
            return 10_000 + record.year
        if record.year is not None and record.year <= requested_year:
            return record.year
        return 0
