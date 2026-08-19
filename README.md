# README

## Lejktor

### Download

- https://www.getlektor.com/docs/installation/

### Usages

- https://www.getlektor.com/docs/

## Footnotes become margin notes

Write an ordinary markdown footnote in any content field:

```
…people who live in the area know it well.[^1]

[^1]: The note itself.
```

`assets/static/sidenotes.js`, loaded from every `templates/layout*.html`, lifts
each note out of the list at the foot of the page into an `<aside class="sidenote">`
placed after the block that cites it. From 1280px up the note sits in a strip
reserved inside the text column's own right padding; narrower than that it stays
in flow as a framed block under the paragraph. The strip is reserved rather than
taken from whatever space happens to be free beside the column, so the note lands
in the same place on a laptop and on a wide display, and can never push the page
sideways. Styling is at the end of `assets/static/style.css`.

Two things to know before writing one:

- **Numbering is per field, so the script renumbers the page.** `software-report.html`
  renders `/software`'s `intro` above the post's own `body`, and mistune numbers each
  field from 1, so such a page restarts at 1 halfway down and emits a second
  `fnref-1` — invalid HTML, and two markers both reading "1". The script renumbers
  across the whole document, so do not expect the numbers in the `.lr` source to
  match the numbers on the page.
- **A reference inside a list item anchors to the whole list.** `<aside>` cannot sit
  between two `<li>`, so below 1280px that note drops to the end of the list instead
  of under its own line. Fine for one note; three references in one list put three
  notes together at the bottom.

With JavaScript off the footnotes simply stay where mistune put them.

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
