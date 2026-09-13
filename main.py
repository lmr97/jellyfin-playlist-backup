import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import requests
from pathlib import Path

from caching import read_cache_files, refresh_cache
from jellyfin.api import PlaylistFull, PlaylistUpdateRequest, LibraryItem

BASE_URL = "https://jellyfin.lmrsvr.net"


def sanitize_path(path: str) -> str:
    invalid_chars   = ["/", "\\", "\"", "’", "?", ":", "<", ">", "*", "|"]

    for char in invalid_chars:
        if char in path:
            path = path.replace(char, "_")

    if path[-1] == ".":
        path = path[:-1] + "_"

    if path[0] == ".":
        path = "_" + path[1:]

    return path


def gen_update_payloads(
        m3u_dir: Path, 
        song_data: list[LibraryItem], 
        pl_data: list[PlaylistFull], 
        skip_names: list[str]
    ) -> list[PlaylistUpdateRequest]:
    
    payloads = []
    for m3u_file in m3u_dir.rglob("*.m3u"):
        print(f"processing file {m3u_file}...")
        with open(m3u_file) as pf:
            file_list = pf.readlines()
            file_list = [f.replace("\n", "") for f in file_list]
            pl_name = m3u_file.parent.stem

            if pl_name in skip_names:
                print("Playlist is to be skipped. Skipping...")
                continue

            pl_id_res = [p.Id for p in pl_data if sanitize_path(p.Name) == pl_name] or None
            pl_id = pl_id_res[0] if pl_id_res else None
            
            song_ids = [s.Id for s in song_data if s.Path in file_list]
            payload = PlaylistUpdateRequest(
                name=pl_name,
                id=pl_id,
                song_ids=song_ids
            )
            payloads.append(payload)

    return payloads


def make_new_playlist(playlist: PlaylistUpdateRequest, user_id: str, api_session: requests.Session) -> str:

    payload = {
        "Name": playlist.name,
        "Ids": playlist.song_ids,
        "UserId": user_id,
        "MediaType": "Unknown",
        "Users": [
            {
                "UserId": user_id,
                "CanEdit": True
            }
        ],
        "IsPublic": False
    }
    resp = api_session.post(
        f"{BASE_URL}/Playlists",
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()["Id"]



def update_playlists(payloads: list[PlaylistUpdateRequest], api_key: str, user_id: str):

    unowned_playlists = []
    with requests.Session() as sesh:
        sesh.headers["Authorization"] = f"MediaBrowser Token=\"{api_key}\""
        for pl in payloads:
            print(f"Updating playlist {pl.name}...")
            if not pl.id:
                pl_cache_stat = os.stat("playlists.json")

                last_mod = datetime.fromtimestamp(pl_cache_stat.st_mtime, tz=ZoneInfo("America/Denver"))
                print(f"Playlist not found in latest cache (retrieved {last_mod}), creating...")

                try:
                    new_id = make_new_playlist(pl, user_id, sesh)
                except:
                    print("Playlist exists on server already; skipping.")

                continue
                

            url = f"{BASE_URL}/Playlists/{pl.id}/Items"
            resp = sesh.post(
                url, 
                params={
                    "ids": pl.song_ids, 
                    "userId": user_id
                }
            )
            if resp.status_code == 403:
                print("This playlist is not owned by you; you'll need to delete and recreate it.")
                unowned_playlists.append(pl.name)
            else:
                resp.raise_for_status()

    print(f"Unowned playlists: {json.dumps(unowned_playlists, indent=4)}")

    
def main():
    ap = argparse.ArgumentParser(
        prog="jfm3u",
        description="For uploading playlists to Jellyfin from M3U files."
    )
    ap.add_argument(
        "pl_path", 
        metavar="PATH",
        default=".",
        help="Path to folder with .m3u files. Will search current directory if omitted.", 
        type=Path,
        action="store"
    )
    ap.add_argument(
        "-u", "--recache", 
        help="Refresh cached data on songs and playlists from server.", 
        choices=["playlists", "songs"],
        action="store"
    )
    ap.add_argument(
        "--skip",
        help="Playlist names to skip.",
        required=False,
        nargs="*"
    )
    cli_args = ap.parse_args()

    api_key_env_var = "JELLYFIN_API_KEY"
    user_id_env_var = "JELLYFIN_USER_ID"
    api_key = os.environ.get(api_key_env_var)
    user_id = os.environ.get(user_id_env_var)

    if not api_key or not user_id:
        raise LookupError(f"Cannot find value for either {api_key_env_var} or {user_id_env_var} in environment.")

    song_data, playlist_data = [{}], [{}]
    if cli_args.recache:
        song_data, playlist_data = refresh_cache(api_key, user_id, cli_args.recache)
    else:
        song_data, playlist_data = read_cache_files()

    skip_pl_names = cli_args.skip
    skip_pl_names = [
        "playlist", 
        "playlists", 
        "deconstructed club", 
        "for sabrina _3", 
        "Heavy Dubstep",
        "Conscious Rap",
        "Music for MASSIVE Speakers",
        "SWEET HYPE",
        "Trance",
        "Spooky Flavors!",
        "Public Freshness",
        "Christmas Specialties",
        "Sounds of Dallas",
        "webfeet",
        "Hard Rock _ Metalcore",
        "Chillin'_ Night Vibes",
        "Rave Faves",
        "HardEdge",
        "House",
        "Drum & Bass"
    ]
    sanitized_names = [sanitize_path(n) for n in cli_args.skip]
    skip_pl_names += sanitized_names
    
    payloads = gen_update_payloads(cli_args.pl_path, song_data, playlist_data, skip_pl_names)

    with open("playlistUpdateRequests.json", mode="w") as pur:
        dumpable = [p.model_dump() for p in payloads]
        json.dump(dumpable, pur, indent=4)

    update_playlists(payloads, api_key, user_id)



if __name__ == "__main__":
    main()