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
        "l": "L",
        "liter": "L",
        "litre": "L",
        "升": "L",
        "kg": "kg",
        "千克": "kg",
        "t": "t",
        "tonne": "t",
        "吨": "t",
    }

    _CONVERSIONS = {
        ("kWh", "kWh"): 1.0,
        ("MWh", "kWh"): 1000.0,
        ("m3", "m3"): 1.0,
        ("L", "L"): 1.0,
        ("kg", "kg"): 1.0,
        ("t", "kg"): 1000.0,
        ("t", "t"): 1.0,
        ("kg", "t"): 0.001,
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
