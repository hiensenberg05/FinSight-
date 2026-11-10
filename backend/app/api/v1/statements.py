from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models import User
from backend.app.services.ingestion_service import IngestionService
from backend.app.schemas.analytics import IngestionResult

router = APIRouter(prefix="/statements", tags=["Statements"])


@router.post("/upload", response_model=IngestionResult)
async def upload_statement(
    statement: UploadFile = File(...),
    bank: str = Form("HDFC"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not statement.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV statement uploads are supported.")

    content = (await statement.read()).decode("utf-8", errors="ignore")
    result = await IngestionService.parse_and_import_csv(
        db=db,
        user_id=user.id,
        bank=bank,
        content=content,
        filename=statement.filename,
    )
    return IngestionResult(
        success=result["success"],
        importedRows=result.get("importedRows", 0),
        message=result.get("message", "Processed statement."),
        bank=bank,
    )
