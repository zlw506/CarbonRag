from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.carbon.factor_loader import FactorLoadError
from app.carbon.schemas import CalcCarbonRequest, CalcCarbonResponse
from app.carbon.service import CarbonService, get_carbon_service

router = APIRouter()


@router.post("/calc-carbon", response_model=CalcCarbonResponse)
def calculate_carbon(
    payload: CalcCarbonRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> CalcCarbonResponse:
    service: CarbonService = get_carbon_service()
    try:
        return service.calculate(owner_user_id=current_user.user_id, payload=payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FactorLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Carbon calculation failed: {exc}")
