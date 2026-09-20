from pathlib import Path
from pydantic import BaseModel, Field

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

class UserPermissions(BaseModel):
    UserId: str
    CanEdit: bool = True

class PlaylistRequestBase(BaseModel):
    Name: str
    Ids: list[str]
    Users: list[UserPermissions]
    IsPublic: bool = False

class PlaylistUpdateRequest(PlaylistRequestBase):
    # field doesn't exist for this model in API; simply 
    # used to keep track of the value here in the program
    Id: str 

class PlaylistCreateRequest(PlaylistRequestBase):
    UserId: str
    MediaType: str = "Audio"