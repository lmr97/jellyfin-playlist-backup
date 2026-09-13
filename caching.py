import json
import requests

from jellyfin.api import PlaylistFull, LibraryItem, APIResponse

BASE_URL = "https://jellyfin.lmrsvr.net"

def read_cache_files(song_file: str = "./cache/songs.json", playlists_file: str = "./cache/playlists.json") -> tuple[list[LibraryItem], list[PlaylistFull]]:
    song_data = []
    playlist_data = []
    with open(song_file) as sf:
        song_data_dict = json.load(sf)
        song_data = [LibraryItem.model_validate(s) for s in song_data_dict["Items"]]

    with open(playlists_file) as pf:
        playlist_data_dict = json.load(pf)
        playlist_data = [PlaylistFull.model_validate(pl) for pl in playlist_data_dict]

    return (song_data, playlist_data)


def refresh_cache(api_key: str, user_id: str, which: str) -> tuple[list[LibraryItem], list[PlaylistFull]]:

    song_data, playlist_data = read_cache_files()

    with requests.Session() as sesh:
        sesh.headers["Authorization"] = f"MediaBrowser Token=\"{api_key}\""

        if which == "songs":
            song_data = refresh_song_cache(user_id, sesh)
        elif which == "playlists":
            playlist_data = refresh_playlist_cache(user_id, sesh)

        return (song_data, playlist_data)


def refresh_playlist_cache(
        user_id: str, 
        session: requests.Session, 
        include_songs: bool = False,
        dump_file_name: str = "playlists.json"
    ) -> list[PlaylistFull]:

    print("Refreshing playlist info cache...")
    url = f"{BASE_URL}/Items"
    query = {
        "includeItemTypes": "Playlist",
        "recursive": True,
    }
    playlist_resp = session.get(url, params=query)
    playlist_resp.raise_for_status()
    resp_content = playlist_resp.json()
    playlist_metadata = APIResponse.model_validate(resp_content)

    playlists_full: list[PlaylistFull] = []

    # populate custom "Songs" property
    # with song info
    for pl in playlist_metadata.Items:
        song_list = []
        if include_songs:
            url = f"{BASE_URL}/Playlists/{pl.Id}/Items"
            song_list_resp = session.get(url, params={"userId": user_id, "fields": ["Path"]})
            song_list_resp_content = APIResponse.model_validate(song_list_resp.json())
            song_list = song_list_resp_content.Items
        plf = PlaylistFull(**pl.model_dump(), Songs=song_list)
        playlists_full.append(plf)


    with open(dump_file_name, mode="w") as playlist_file:
        dumpable = [pl.model_dump() for pl in playlists_full]
        json.dump(dumpable, playlist_file, indent=4)

    print("Playlists refreshed.")

    return playlists_full


def refresh_song_cache(user_id: str, session: requests.Session) -> list[LibraryItem]:

    url = f"{BASE_URL}/Items"
    query = {
        "sortBy": "SortName",
        "includeItemTypes": "Audio",
        "recursive": True,
        "fields": ["Path"]
    }
    
    print("Refreshing song info cache...")
    songs_resp = session.get(url, params=query)
    songs_resp.raise_for_status()
    song_data = songs_resp.json()

    with open("songs.json", mode="w") as song_file:
        json.dump(song_data, song_file, indent=4)

    print("Songs refreshed.")

    return song_data["Items"]