from pydantic import BaseModel
from typing import Optional


class NormalizedEvent(BaseModel):
    is_schema_change: bool
    table_name: Optional[str]
    table_id: Optional[str]