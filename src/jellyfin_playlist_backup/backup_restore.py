from argparse import Namespace
from datetime import datetime
import json
from enum import Enum
import requests
import sys
from urllib.parse import urlparse

from pydantic import BaseModel

from jellyfin.api import PlaylistFull, LibraryItem, PlaylistCreateRequest, PlaylistUpdateRequest, APIResponse, UserPermissions
from utilities import get_auth_from_env, BASE_URL


class Backup(str, Enum):
    STANDARD = "standard"
    FULL = "full"

class PlaylistsBackup[PlaylistType](BaseModel):
    backup_type: Backup
    created: datetime
    content: list[PlaylistType]

    @property
    def is_full(self) -> bool:
        return self.backup_type == Backup.FULL


def back_up_playlists(cli_args: Namespace):

    print("Playlist backup started.", file=sys.stderr)

    api_key, user_id = get_auth_from_env()

    base_url = cli_args.url or BASE_URL
    url = f"{base_url}/Items"
    query = {
        "includeItemTypes": "Playlist",
        "recursive": True,
    }

    with requests.Session() as session:
        session.headers["Authorization"] = f"MediaBrowser Token=\"{api_key}\""
        playlist_resp = session.get(url, params=query)
        playlist_resp.raise_for_status()
        resp_content = playlist_resp.json()
        playlist_metadata = APIResponse.model_validate(resp_content)

        playlists = []

        for pl in playlist_metadata.Items:
            print(f"Backing up {pl.Name}...", file=sys.stderr)
            song_list = []
        
            url = f"{base_url}/Playlists/{pl.Id}/Items"
            song_list_resp = session.get(url, params={"userId": user_id, "fields": ["Path"]})
            song_list_resp_content = APIResponse.model_validate(song_list_resp.json())
            song_list = song_list_resp_content.Items

            plp: PlaylistFull | PlaylistUpdateRequest
            if cli_args.full:
                plp = PlaylistFull(**pl.model_dump(), Songs=song_list)
            else:
                songs_ids = [s.Id for s in song_list]
                plp = PlaylistUpdateRequest(
                    Name=pl.Name, 
                    Id=pl.Id,
                    Users=[UserPermissions(UserId=user_id, CanEdit=True)],
                    Ids=songs_ids
                )
            if plp.Name in cli_args.skip:
                print(f"{plp.Name} in skip list, skipping...", file=sys.stderr)
                continue
            
            playlists.append(plp)
            

    bk_type = Backup.FULL if cli_args.full else Backup.STANDARD
    backup = PlaylistsBackup(
        backup_type=bk_type, 
        created=datetime.now(),
        content=playlists
    )
    raw_backup = backup.model_dump_json(indent=4)

    if cli_args.output == "-":
        print(raw_backup)
        return
    else:
        with open(cli_args.output, mode="w+") as playlist_file:
            playlist_file.write(raw_backup)

    msg = "Playlist backup complete."
    if cli_args.full:
        msg = "Playlist backup with full playlist and song info completed."

    print(msg)


def restore_playlists(cli_args: Namespace):

    api_key, user_id = get_auth_from_env()
    unowned_playlists = []

    backup: PlaylistsBackup[PlaylistUpdateRequest]
    payloads: list[PlaylistUpdateRequest] = []
    with open(cli_args.file) as backup_file:
        backup_raw = json.load(backup_file)
        backup = PlaylistsBackup[PlaylistUpdateRequest].model_validate(backup_raw)
        payloads = backup.content

    if backup.is_full:
        raise NotImplementedError(
            "The backup referenced is a full backup, which is "
            "intended to be raw material for an arbitrary restoration "
            "method. Slim it down to a create/update-formatted "
            "backup with jq or a similar utility."
        )

    with requests.Session() as sesh:
        sesh.headers["Authorization"] = f"MediaBrowser Token=\"{api_key}\""

        url = f"{BASE_URL}/Playlists"
        for pl in payloads:
            print(f"Updating playlist {pl.Name}...", file=sys.stderr)

            req_url = url

            # Id field doesn't exist in Jellyfin API schema for this model
            update_payload = pl.model_dump(exclude={"Id"})

            # currently not working via the API
            if cli_args.mode == "update":
                req_url = f"{url}/{pl.Id}"

            elif cli_args.mode == "create":
                pcr = PlaylistCreateRequest(**update_payload, UserId=user_id)
                update_payload = pcr.model_dump()

            if cli_args.dry_run:
                print("On dry-run mode. Here's the request that would be sent to the server:")
                print("\n--- HTTP request ---")
                url_parsed = urlparse(req_url)
                print(f"POST {url_parsed.path} HTTP/1.1")
                print(f"Host: {url_parsed.hostname}")
                for k, v in sesh.headers.items():
                    print(f"{k}: {v}")
                print()
                print(json.dumps(update_payload, indent=4))
                continue

            if pl.Name in cli_args.skip:
                print(f"{pl.Name} in skip list, skipping...", file=sys.stderr)
                continue

            resp = sesh.post(req_url, json=update_payload)

            if resp.status_code == 403:
                print("This playlist is not owned by you; you'll need to delete and recreate it.", file=sys.stderr)
                unowned_playlists.append(pl.Name)
            else:
                resp.raise_for_status() 

    print(f"Unowned playlists: {json.dumps(unowned_playlists, indent=4)}")


def refresh_song_cache(session: requests.Session) -> list[LibraryItem]:

    url = f"{BASE_URL}/Items"
    query = {
        "sortBy": "SortName",
        "includeItemTypes": "Audio",
        "recursive": True,
        "fields": ["Path"]
    }
    
    print("Refreshing song info cache...", file=sys.stderr)
    songs_resp = session.get(url, params=query)
    songs_resp.raise_for_status()
    song_data = songs_resp.json()

    with open("songs.json", mode="w") as song_file:
        json.dump(song_data, song_file, indent=4)

    print("Songs refreshed.", file=sys.stderr)

    return song_data["Items"]