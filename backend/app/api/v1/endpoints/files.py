from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.files.schemas import UploadedFileResponse
from app.files.service import FileService, get_file_service

router = APIRouter()


@router.post("/files", response_model=UploadedFileResponse)
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> UploadedFileResponse:
    service: FileService = get_file_service()
    try:
        uploaded = service.save_upload(
            owner_user_id=current_user.user_id,
            session_id=session_id,
            filename=file.filename or "upload.bin",
            mime_type=file.content_type or "application/octet-stream",
            content=await file.read(),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except TypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    finally:
        await file.close()

    return UploadedFileResponse.model_validate(uploaded.model_dump())
