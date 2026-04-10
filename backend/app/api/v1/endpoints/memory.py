from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.memory.schemas import CreateMemoryNoteRequest, MemoryNote, UpdateMemoryNoteRequest
from app.memory.service import get_memory_service

router = APIRouter(prefix="/memory-notes")


@router.get("", response_model=list[MemoryNote])
def list_memory_notes(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> list[MemoryNote]:
    return get_memory_service().list_notes(owner_user_id=current_user.user_id)


@router.post("", response_model=MemoryNote)
def create_memory_note(
    payload: CreateMemoryNoteRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> MemoryNote:
    return get_memory_service().create_note(owner_user_id=current_user.user_id, payload=payload)


@router.patch("/{memory_note_id}", response_model=MemoryNote)
def update_memory_note(
    memory_note_id: str,
    payload: UpdateMemoryNoteRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> MemoryNote:
    updated = get_memory_service().update_note(
        owner_user_id=current_user.user_id,
        memory_note_id=memory_note_id,
        payload=payload,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Memory note not found.")
    return updated


@router.delete("/{memory_note_id}")
def delete_memory_note(
    memory_note_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict[str, str]:
    deleted = get_memory_service().delete_note(
        owner_user_id=current_user.user_id,
        memory_note_id=memory_note_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory note not found.")
    return {"status": "ok"}
