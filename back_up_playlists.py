from datetime import datetime
import os
import requests

from caching import refresh_playlist_cache

def main():    
    api_key_env_var = "JELLYFIN_API_KEY"
    user_id_env_var = "JELLYFIN_USER_ID"
    api_key = os.environ.get(api_key_env_var)
    user_id = os.environ.get(user_id_env_var)

    if not api_key or not user_id:
        raise LookupError(f"Cannot find value for either {api_key_env_var} or {user_id_env_var} in environment.")

    now = datetime.now().replace(microsecond=0)
    timestamp = now.isoformat()
    backup_name = f"playlistBackup_{timestamp}.json"

    with requests.Session() as sesh:
        refresh_playlist_cache(
            user_id, 
            sesh, 
            include_songs=True,
            dump_file_name=backup_name
        )


if __name__ == "__main__":
    main()