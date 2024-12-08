from typing import Optional

from pydantic import BaseModel


class TBAPageEtag(BaseModel):
    id: Optional[int] = None
    page_num: Optional[int] = None
    etag: str
    endpoint: str
    year: int
