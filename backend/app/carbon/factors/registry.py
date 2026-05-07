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
        if activity.requested_factor_id:
            requested = [record for record in candidates if record.factor_id == activity.requested_factor_id]
            if requested:
                return self._finalize_selection(requested[0], activity, warnings)
            warnings.append(
                f"未找到用户指定因子 {activity.requested_factor_id}，已按系统优先级选择可用因子。"
            )

        method_candidates = self._filter_by_method(candidates, activity)
        if method_candidates:
            candidates = method_candidates

        selected = sorted(
            candidates,
            key=lambda record: (
                self._source_score(record),
                self._region_score(record, activity),
                self._year_score(record, activity.year),
                int(record.is_default),
            ),
            reverse=True,
        )[0]

        return self._finalize_selection(selected, activity, warnings)

    def _finalize_selection(
        self,
        selected: FactorRecord,
        activity: CarbonActivityItem,
        warnings: list[str],
    ) -> FactorSelection:
        if selected.source_type == "guidance_default":
            warnings.append(
                "当前使用 guidance_default 燃料缺省因子：该因子来源于公共机构核算指南缺省值，"
                "仅用于基础演示和缺少更权威因子时参考；企业正式核算应优先使用国家温室气体排放因子数据库或适用行业指南。"
            )
        elif selected.source_type == "demo":
            warnings.append(
                f"{selected.factor_id} 是 demo 因子，仅用于链路验证，不用于正式盘查或审计。"
            )

        requested_location = activity.province or activity.region
        selected_location = selected.region_code or selected.region
        if requested_location and selected_location != requested_location:
            warnings.append(
                f"{activity.activity_name} 未命中请求地区 {requested_location}，使用 {selected_location or 'global'} 因子。"
            )
        if activity.year and selected.year and selected.year != activity.year:
            warnings.append(
                f"{activity.activity_name} 未命中请求年份 {activity.year}，使用 {selected.year} 因子。"
            )
        if activity.factor_preference == "official_latest" and selected.source_type not in {"official"}:
            warnings.append(
                f"{activity.activity_name} 未命中官方因子，已回退到 {selected.source_type} 因子。"
            )

        return FactorSelection(factor=selected, warnings=list(dict.fromkeys(warnings)))

    @staticmethod
    def _filter_by_method(candidates: list[FactorRecord], activity: CarbonActivityItem) -> list[FactorRecord]:
        if activity.scope == "scope2" and activity.activity_category == "purchased_electricity":
            wanted = activity.scope2_method or "location_based"
            exact = [record for record in candidates if (record.method_type or "location_based") == wanted]
            if exact:
                return exact
        return candidates

    @staticmethod
    def _source_score(record: FactorRecord) -> int:
        if record.source_priority:
            return record.source_priority
        if record.source_type == "official" or record.is_official:
            return 60
        if record.source_type == "guidance_default":
            return 30
        if record.source_type == "demo":
            return 10
        return 0

    @staticmethod
    def _region_score(record: FactorRecord, activity: CarbonActivityItem) -> int:
        requested_region = activity.region
        requested_province = activity.province
        record_region = record.region_code or record.region
        if requested_province and record_region == requested_province:
            return 500
        if requested_region and record_region == requested_region:
            return 400
        if record.region_level == "national" or record_region == "CN":
            return 200
        if record_region is None:
            return 100
        return 0

    @staticmethod
    def _year_score(record: FactorRecord, requested_year: int | None) -> int:
        record_year = record.effective_year or record.year
        if requested_year is None:
            return record_year or 0
        if record_year == requested_year:
            return 10_000 + record_year
        if record_year is not None and record_year <= requested_year:
            return record_year
        return 0
