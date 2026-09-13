from pathlib import Path
from pydantic import BaseModel

class LibraryItem(BaseModel):
    Name: str
    ServerId: str
    Id: str
    RunTimeTicks: int
    IsFolder: bool
    Type: str
    ImageTags: dict = {}
    BackdropImageTags: list = []
    ImageBlurHashes: dict = {}
    LocationType: str
    MediaType: str
    ChannelId: str | None = None
    Path: str | None = None

class APIResponse(BaseModel):
    Items: list[LibraryItem]
    TotalRecordCount: int
    StartIndex: int

class PlaylistFull(LibraryItem):
    Songs: list[LibraryItem]

class PlaylistUpdateRequest(BaseModel):
    name: str
    id: str | None
    song_ids: list[str]