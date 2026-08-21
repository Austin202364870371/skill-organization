---
name: Robust Pagination and Deduplication for Spotify Library CSV Export
description: Handles paginated API calls, deduplicates songs across library sources, and safely formats CSV data with multiple artists, missing metadata, and failure handling.
---

## When to Use
Use when the library export requires robust handling of duplicates, missing metadata, multi-artist songs, or when the primary workflow may fail due to incomplete data.

## Preconditions
- Spotify and file system access tokens are available.
- The output CSV path is known.

## Procedure
1. Always use a pagination helper that stops on an empty page; never assume a fixed number of pages.
2. Use a set for song IDs to avoid duplicates from overlapping album/playlist membership.
3. When fetching song details, handle possible missing artists: if the song object has no `artists`, use an empty string.
4. For songs with multiple artists, fetch each artist name and join with `|` in the same order returned.
5. CSV-escape fields containing commas or newlines by wrapping them in double quotes (use `csv` module or equivalent).
6. If a target file already exists, overwrite it with `file_system.create_file`.
7. Always write the file before any destructive account action (e.g., `delete_account`).

## Failure Handling
- On token expiration, re-login and retry.
- If a requested song or artist ID no longer exists, skip it and log a warning.
- If `create_file` fails, do not proceed to `delete_account`; notify the user.

## Verification
- Check the file size is non-zero.
- Check the header line matches exactly `Title,Artists`.
- Ensure all artist separators are `|`.
- Confirm the number of rows equals the number of unique song titles in the set.

## Relevant APIs / Tools
- apis.spotify.show_song_library
- apis.spotify.show_album_library
- apis.spotify.show_playlist_library
- apis.spotify.show_song
- apis.spotify.show_artist
- apis.file_system.create_file
- apis.file_system.login

## Examples
```python
# Example: safely get artist names, skipping any that fail
def safe_artist_names(song):
    names = []
    for artist in getattr(song, 'artists', []):
        try:
            names.append(apis.spotify.show_artist(artist_id=artist.id).name)
        except Exception:
            continue
    return '|'.join(names)
```

```python
# Example: build a properly escaped CSV
import csv, io
out = io.StringIO()
writer = csv.writer(out)
writer.writerow(['Title', 'Artists'])
for title, artists in rows.items():
    writer.writerow([title, artists])
content = out.getvalue()
```
