from app.carbon.schemas import CarbonUnitConversionTrace


class UnitConverter:
    _ALIASES = {
        "kwh": "kWh",
        "kw·h": "kWh",
        "千瓦时": "kWh",
        "mwh": "MWh",
        "m3": "m3",
        "nm3": "m3",
        "立方米": "m3",
        "方": "m3",
        "km": "km",
        "公里": "km",
        "千米": "km",
        "人公里": "人公里",
        "人·公里": "人公里",
        "人-公里": "人公里",
        "人千米": "人公里",
        "pkm": "人公里",
        "吨公里": "吨公里",
        "吨·公里": "吨公里",
        "吨-公里": "吨公里",
        "tkm": "吨公里",
        "m2": "m2",
        "m²": "m2",
        "㎡": "m2",
        "平方米": "m2",
        "l": "L",
        "liter": "L",
        "litre": "L",
        "升": "L",
        "kg": "kg",
        "千克": "kg",
        "公斤": "kg",
        "g": "g",
        "克": "g",
        "t": "t",
        "tonne": "t",
        "吨": "t",
        "件": "件",
        "个": "个",
        "台": "台",
        "张": "张",
        "只": "只",
        "次": "次",
        "人次": "人次",
        "间夜": "间夜",
    }

    _CONVERSIONS = {
        ("kWh", "kWh"): 1.0,
        ("MWh", "kWh"): 1000.0,
        ("m3", "m3"): 1.0,
        ("L", "L"): 1.0,
        ("kg", "kg"): 1.0,
        ("g", "kg"): 0.001,
        ("kg", "g"): 1000.0,
        ("t", "kg"): 1000.0,
        ("t", "t"): 1.0,
        ("kg", "t"): 0.001,
        ("km", "km"): 1.0,
        ("人公里", "人公里"): 1.0,
        ("吨公里", "吨公里"): 1.0,
        ("m2", "m2"): 1.0,
        ("件", "件"): 1.0,
        ("个", "个"): 1.0,
        ("台", "台"): 1.0,
        ("张", "张"): 1.0,
        ("只", "只"): 1.0,
        ("次", "次"): 1.0,
        ("人次", "人次"): 1.0,
        ("间夜", "间夜"): 1.0,
    }

    def normalize(
        self,
        *,
        activity_name: str,
        value: float,
        from_unit: str,
        to_unit: str,
    ) -> tuple[float, CarbonUnitConversionTrace]:
        normalized_from = self._canonical(from_unit)
        normalized_to = self._canonical(to_unit)
        if normalized_from == normalized_to:
            return round(float(value), 6), CarbonUnitConversionTrace(
                activity_name=activity_name,
                input_value=round(float(value), 6),
                input_unit=from_unit,
                normalized_value=round(float(value), 6),
                normalized_unit=normalized_to,
                conversion_factor=1.0,
            )
        key = (normalized_from, normalized_to)
        if key not in self._CONVERSIONS:
            raise ValueError(f"Unsupported unit conversion: {from_unit} -> {to_unit}")
        factor = self._CONVERSIONS[key]
        normalized_value = round(float(value) * factor, 6)
        return normalized_value, CarbonUnitConversionTrace(
            activity_name=activity_name,
            input_value=round(float(value), 6),
            input_unit=from_unit,
            normalized_value=normalized_value,
            normalized_unit=normalized_to,
            conversion_factor=factor,
        )

    def _canonical(self, unit: str) -> str:
        normalized = unit.strip()
        return self._ALIASES.get(normalized.lower(), normalized)
