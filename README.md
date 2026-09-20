# Jellyfin Playlist Backup/Restore Utility

Uses the API to back up to JSON files, which can be used to restore from.

This was mostly made for me. But I'm putting it here in case anyone else has use for it.

## Installation

The best way to go is with `pipx` or `uv tool`. I'll illustrate with `uv tool`:

```{bash}
git clone https://github.com/lmr97/jellyfin-playlist-backup
cd jellyfin-playlist-backup
uv tool install .
```