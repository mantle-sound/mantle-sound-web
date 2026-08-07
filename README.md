# README

## Lejktor

### Download

- https://www.getlektor.com/docs/installation/

### Usages

- https://www.getlektor.com/docs/

## Demonstration packages

`assets/files/software/260115-002-birdidpv/` is entirely derived — no file in it
is hand-edited. `tools/build_birdidpv_package.py` is the definition of how it is
built, in stages that cost very different amounts:

```sh
python3 tools/build_birdidpv_package.py            # render + site, seconds
python3 tools/build_birdidpv_package.py check      # fail if anything drifted
python3 tools/build_birdidpv_package.py all        # re-run BirdNET, minutes
```

`check` regenerates the reports in memory and compares them byte for byte with
what is on disk. Run it before committing a change to the package or to
`tools/birdidpv_site_pages.py`.

Only `all` needs the source WAV, which lives on removable media, and a `birdidpv`
built with the `birdnet` extra. Pass `--source` and `--birdidpv` if they are
somewhere else.

The split matters: [field-audio-tools](https://github.com/) is a standalone
toolkit for anyone holding a recording, and produces bare HTML and CSV that owe
nothing to this site. Everything site-shaped — the styled pages, the
`-bare` filenames, the reuse of lowdom's preview audio — is decided here, in
`tools/`, and never pushed back into the tool.
