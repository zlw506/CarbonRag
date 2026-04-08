import json
from functools import lru_cache
from pathlib import Path

from app.carbon.schemas import CarbonFactor
from app.core.config import REPO_ROOT, get_settings


def resolve_factor_file(factor_file: Path | str | None = None) -> Path:
    if factor_file is not None:
        path = Path(factor_file)
        return path if path.is_absolute() else REPO_ROOT / path

    factor_dir = Path(get_settings().factor_data_dir)
    resolved_dir = factor_dir if factor_dir.is_absolute() else REPO_ROOT / factor_dir
    return resolved_dir / "carbon_factors_v0_1_9a.json"


class FactorLoadError(RuntimeError):
    """Raised when factor data cannot be loaded or validated."""


class CarbonFactorLoader:
    def __init__(self, factor_file: Path | str | None = None) -> None:
        self.factor_file = resolve_factor_file(factor_file)

    def load(self) -> dict[str, CarbonFactor]:
        if not self.factor_file.exists():
            raise FactorLoadError(f"Factor file not found: {self.factor_file}")

        try:
            payload = json.loads(self.factor_file.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise FactorLoadError(f"Unable to decode factor file: {self.factor_file}") from exc
        except json.JSONDecodeError as exc:
            raise FactorLoadError(f"Factor file is not valid JSON: {self.factor_file}") from exc

        raw_factors = payload.get("factors")
        if not isinstance(raw_factors, list) or not raw_factors:
            raise FactorLoadError("Factor file must contain a non-empty 'factors' list.")

        factors: dict[str, CarbonFactor] = {}
        for raw_factor in raw_factors:
            try:
                factor = CarbonFactor.model_validate(raw_factor)
            except Exception as exc:  # pragma: no cover - pydantic specifics are covered by tests
                raise FactorLoadError("Factor payload validation failed.") from exc
            factors[factor.item] = factor

        required_items = {"electricity", "natural_gas", "diesel"}
        missing = required_items.difference(factors)
        if missing:
            raise FactorLoadError(f"Factor file is missing required items: {sorted(missing)}")

        return factors


@lru_cache(maxsize=1)
def get_factor_loader() -> CarbonFactorLoader:
    return CarbonFactorLoader()
