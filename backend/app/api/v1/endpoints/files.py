from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.files.schemas import UploadedFileResponse
from app.files.service import FileService, get_file_service

router = APIRouter()


@router.post("/files", response_model=UploadedFileResponse)
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> UploadedFileResponse:
    service: FileService = get_file_service()
    try:
        uploaded = service.save_upload(
            session_id=session_id,
            filename=file.filename or "upload.bin",
            mime_type=file.content_type or "application/octet-stream",
            content=await file.read(),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="会话不存在。")
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except TypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    finally:
        await file.close()

    return UploadedFileResponse.model_validate(uploaded.model_dump())
