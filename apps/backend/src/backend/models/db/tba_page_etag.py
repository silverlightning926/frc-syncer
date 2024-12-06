from pydantic import BaseModel
from typing import Optional


class TBAPageEtag(BaseModel):
    page_num: Optional[int] = None
    etag: str
    endpoint: str
    year: int
