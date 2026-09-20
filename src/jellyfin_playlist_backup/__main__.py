from argparse import ArgumentParser, Namespace

from .backup_restore import back_up_playlists, restore_playlists


def parse_cli_args() -> Namespace:
    ap = ArgumentParser(
        prog="jfpl",
        description="Backs up and restores playlists on Jellyfin."
    )

    sub_ap = ap.add_subparsers() 
    backup = sub_ap.add_parser("backup", help="Back up playlists to file")
    backup.add_argument(
        "--output", "-o", 
        dest="output",
        help="Write backup data to JSON file. Normally is formatted as a " + 
            "list of objects that can be used as payloads to create playlists " +
            "via the API, unless --full is specified. Defaults to stdout.",
        type=str,
        metavar="FILE",
        default="-"
    )
    backup.add_argument(
        "--full", "-a", 
        help="Whether to generate a file that includes all song info and playlist " + 
            "metadata, instead of an array of playlist creation payloads.",
        action="store_true"
    )
    backup.add_argument(
        "--skip",
        dest="skip",
        help="Playlist names to skip. (needs more work to be functional)",
        required=False,
        default=[],
        nargs="*"
    )
    backup.add_argument(
        "--url",
        help="Base URL, overrides the hardcoded one."
    )
    backup.set_defaults(func=back_up_playlists)

    restore = sub_ap.add_parser("restore", help="Restore playlists from file")
    restore.add_argument(
        "--file", "-f",
        type=str,
        help="Restore playlists from this file."
    )
    restore.add_argument(
        "--mode", "-m",
        help="Whether to create a new playlist with the backup ('create') or " + 
            "set the list of songs for a playlist of the same name ('update'). " +
            "This overwrites the existing songs in the playlist.",
        default="update",
        choices=["create", "update"]
    )
    restore.add_argument(
        "--dry-run",
        help="Don't send request to server; dump the request info into the terminal.",
        action="store_true"
    )
    restore.add_argument(
        "--skip",
        dest="skip",
        help="Playlist names to skip.",
        required=False,
        default=[],
        nargs="*"
    )
    restore.set_defaults(func=restore_playlists)
    
    return ap.parse_args()

    
def main():
    cli_args = parse_cli_args()
    cli_args.func(cli_args)  # run relevant command


if __name__ == "__main__":
    main()