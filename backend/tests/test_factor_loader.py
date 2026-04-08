import json

import pytest

from app.carbon.factor_loader import CarbonFactorLoader, FactorLoadError


def build_factor_payload() -> dict:
    return {
        "version": "v0.1.9a",
        "factors": [
            {
                "factor_id": "factor-electricity",
                "item": "electricity",
                "name": "Electricity Demo Factor",
                "unit": "kgCO2e/kWh",
                "value": 0.57,
                "source": "Demo Source",
                "source_url": "https://example.com/electricity",
                "note": "demo",
                "version": "v0.1.9a",
            },
            {
                "factor_id": "factor-natural-gas",
                "item": "natural_gas",
                "name": "Natural Gas Demo Factor",
                "unit": "kgCO2e/m3",
                "value": 2.162,
                "source": "Demo Source",
                "source_url": "https://example.com/gas",
                "note": "demo",
                "version": "v0.1.9a",
            },
            {
                "factor_id": "factor-diesel",
                "item": "diesel",
                "name": "Diesel Demo Factor",
                "unit": "kgCO2e/L",
                "value": 2.63,
                "source": "Demo Source",
                "source_url": "https://example.com/diesel",
                "note": "demo",
                "version": "v0.1.9a",
            },
        ],
    }


def test_factor_loader_reads_expected_factor_items(tmp_path) -> None:
    factor_file = tmp_path / "factors.json"
    factor_file.write_text(json.dumps(build_factor_payload(), ensure_ascii=False), encoding="utf-8")

    factors = CarbonFactorLoader(factor_file).load()

    assert set(factors) == {"electricity", "natural_gas", "diesel"}
    assert factors["electricity"].value == 0.57


def test_factor_loader_raises_when_json_is_invalid(tmp_path) -> None:
    factor_file = tmp_path / "broken.json"
    factor_file.write_text("{not-json", encoding="utf-8")

    with pytest.raises(FactorLoadError):
        CarbonFactorLoader(factor_file).load()


def test_factor_loader_raises_when_required_item_missing(tmp_path) -> None:
    payload = build_factor_payload()
    payload["factors"] = payload["factors"][:2]
    factor_file = tmp_path / "missing.json"
    factor_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(FactorLoadError):
        CarbonFactorLoader(factor_file).load()
