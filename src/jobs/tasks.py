from typing import Any

from jobs.broker import broker
from services.exports import ExportService


@broker.task
async def export_transactions(params: dict[str, Any]) -> str:
    return await ExportService.export_transactions(params)
