from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.carbon.factor_loader import CarbonFactorLoader


def _join(values: set[str | None], *, fallback: str = "-") -> str:
    cleaned = sorted({str(value).strip() for value in values if value})
    return ", ".join(cleaned[:8]) if cleaned else fallback


def generate_index(output_path: Path) -> None:
    records = CarbonFactorLoader().load_registry().records
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for record in records:
        grouped[(record.activity_category or "-", record.activity_name or "-")].append(record)

    lines: list[str] = [
        "# CarbonRag Carbon Factor Index",
        "",
        "This is a compact directory for CarbonRag's local carbon factor registry.",
        "Use it to identify candidate activity names before calling `carbon_factor_lookup` for calculation-ready factor values.",
        "",
        f"- registry_record_count: {len(records)}",
        f"- unique_activity_count: {len(grouped)}",
        "- value_source: `carbon_factor_lookup` results, not this index",
        "",
        "## Activity Index",
        "",
        "| Activity category | Activity name | Records | Activity units | Factor units | Example factor IDs |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]

    for (category, name), items in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        units = _join({item.activity_unit for item in items})
        factor_units = _join({item.factor_unit for item in items})
        examples = ", ".join(item.factor_id for item in items[:4])
        lines.append(f"| {category} | {name} | {len(items)} | {units} | {factor_units} | {examples} |")

    lines.extend(
        [
            "",
            "## Common Aliases",
            "",
            "| User wording | Query activity hints |",
            "| --- | --- |",
            "| 外购电力、用电、电量、购电、kWh、度电 | electricity / purchased_electricity |",
            "| 天然气、燃气、natural gas、m3、立方米 | natural_gas / stationary_combustion |",
            "| 柴油、diesel | diesel / stationary_combustion |",
            "| 汽油、gasoline | gasoline / stationary_combustion |",
            "| 液化石油气、LPG | lpg / stationary_combustion |",
            "| 煤、原煤、coal | coal / stationary_combustion |",
            "| 蒸汽、外购蒸汽、steam | steam / purchased_energy |",
            "| 自来水、用水、water | water / water_supply |",
            "| 制冷剂、冷媒、R410A、R134a | refrigerant; current registry may not contain direct refrigerant factors |",
            "",
            "## Known Gaps",
            "",
            "- If `carbon_factor_lookup` returns no hit for a listed alias, answer that the current local registry lacks a calculation-ready factor for that activity.",
            "- Refrigerants such as R410A/R134a are recognized as requested activities, but direct GWP/factor records may be absent in the current seed registry.",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "references" / "carbon-factor-index.md"
    generate_index(target)
