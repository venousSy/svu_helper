import aiohttp
import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from dashboard_api.api.dependencies import get_current_user
from dashboard_api.services.telegram_service import TelegramService

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/files",
    tags=["files"],
    dependencies=[Depends(get_current_user)]
)

async def _stream_file(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Failed to fetch file from Telegram")
            async for chunk in response.content.iter_chunked(8192):
                yield chunk

@router.get("/{file_id}")
async def get_file(file_id: str):
    """
    Proxies the file download from Telegram to bypass CORS and authenticate via dashboard.
    """
    logger.info("Proxying file download", file_id=file_id)
    telegram_service = TelegramService()
    file_url = await telegram_service.get_file_url(file_id)
    
    if not file_url:
        logger.error("Could not retrieve file URL", file_id=file_id)
        raise HTTPException(status_code=404, detail="File not found or unable to fetch from Telegram")
        
    return StreamingResponse(_stream_file(file_url), media_type="application/octet-stream")
