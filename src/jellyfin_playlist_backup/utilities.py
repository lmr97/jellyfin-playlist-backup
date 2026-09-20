import os

BASE_URL = "https://jellyfin.lmrsvr.net"

def get_auth_from_env() -> tuple[str, str]:
    api_key_env_var = "JELLYFIN_API_KEY"
    user_id_env_var = "JELLYFIN_USER_ID"
    api_key = os.environ.get(api_key_env_var)
    user_id = os.environ.get(user_id_env_var)

    if not api_key or not user_id:
        raise LookupError(f"Cannot find value for either {api_key_env_var} or {user_id_env_var} in environment.")

    return (api_key, user_id)


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