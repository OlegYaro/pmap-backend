import csv
import tempfile
import uuid
from pathlib import Path
from typing import Any

from api.schemas.transactions import TransactionResponse
from core.storage import storage
from integrations.extraction import extraction_http_client

PAGE_SIZE = 1000
COLUMNS = list(TransactionResponse.model_fields)


class ExportService:
    @staticmethod
    async def export_transactions(params: dict[str, Any]) -> str:
        """Write all filtered transactions to a CSV file, put it to S3 and return its key."""
        key = f"exports/{uuid.uuid4()}.csv"
        with tempfile.NamedTemporaryFile("w", suffix=".csv", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, COLUMNS)
            writer.writeheader()

            after_id = None
            while True:
                page_params = {**params, "limit": PAGE_SIZE}
                if after_id is not None:
                    page_params["after_id"] = after_id
                page = await extraction_http_client.list_transactions(page_params)
                for row in page:
                    writer.writerow(TransactionResponse.model_validate(row).model_dump(mode="json"))
                if len(page) < PAGE_SIZE:
                    break
                after_id = page[-1]["id"]

            file.flush()
            await storage.put_file(key, Path(file.name))
        return key
