from fastapi import APIRouter, HTTPException

from app.carbon.factor_loader import FactorLoadError
from app.carbon.schemas import CalcCarbonRequest, CalcCarbonResponse
from app.carbon.service import CarbonService, get_carbon_service

router = APIRouter()


@router.post("/calc-carbon", response_model=CalcCarbonResponse)
def calculate_carbon(payload: CalcCarbonRequest) -> CalcCarbonResponse:
    service: CarbonService = get_carbon_service()
    try:
        return service.calculate(payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="会话不存在。")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FactorLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Carbon calculation failed: {exc}")
