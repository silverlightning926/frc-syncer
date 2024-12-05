from pydantic import BaseModel


class TBAPageEtag(BaseModel):
    page_num: int
    etag: str
    endpoint: str
    year: int
