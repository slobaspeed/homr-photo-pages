# Photos of printed template pages, for homr

Phone photos of printed sheet-music pages with ArUco squares around the music. The squares say which page a photo
shows and where each part of the flat page landed, so the printed music can be erased and other music, with an
exact answer, pasted onto the same real paper. Made for [homr](https://github.com/liebharc/homr)'s training; see
[liebharc/homr#206](https://github.com/liebharc/homr/discussions/206).

| Folder | What |
|---|---|
| `photos/train/` | Photos for training: real paper, light and bends to paste songs onto. |
| `photos/test/` | **Test only, never train on these.** 43 photos of pages T43–T50, read against the exact answers in `templates/keys/`. The 10 photos the phone saved sideways were turned upright. |
| `templates/` | `templates.pdf` (pages T23–T50, A4), `templates.json` (where every square and the music sit on each page), `keys/` (the exact MusicXML of the Verovio pages T35–T50), `sources.md` (the music and licence of every page). |
| `make_templates.py` | Makes new template pages (T51 and up) from your own MusicXML. |
| `tools/` | How the photos were cleaned (all metadata removed) and the templates copied. |

## Adding photos

1. Print a page of `templates/templates.pdf` (or a new one from `make_templates.py`) on A4, at 100% size.
2. Photograph it as you would to read it: any light, any phone, tilted or curled. Keep 4 or more squares in the shot.
3. Put the photo in `photos/train/`. The squares tell which page it is; photos of T43–T50 are never used for training.

New pages should use music free of conditions (CC0 or public domain, e.g. OpenScore Lieder), so their photos stay
simple to share.

## Licences

- `photos/train/`: CC BY-SA 4.0 ([LICENSE-photos-train.md](LICENSE-photos-train.md)).
- `photos/test/` and the T43–T50 keys: CC BY-NC-SA 4.0, as the ASAP scores they show ([LICENSE-test.md](LICENSE-test.md)).
- Template pages: the licence of the music on each, listed in [templates/sources.md](templates/sources.md).
- Code: MIT ([LICENSE](LICENSE)).

Made by slobaspeed with Claude (an AI assistant).
