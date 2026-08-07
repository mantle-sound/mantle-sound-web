"""Build the site-styled birdidpv report pages for the Take 002 demo package.

Run through tools/build_birdidpv_package.py rather than directly.

The CLI writes bare HTML 4.01. These are the styled pages the site serves:
report.html (static) and report-js.html (interactive). Site chrome — header,
nav, subfooter, footer, navbar script — is lifted verbatim from the neighbouring
lowdom package at build time, so the two tools' reports cannot drift apart.

Two things here are editorial rather than derived, and are meant to be edited by
hand as the analysis improves: SUSPECT, the species this report asks readers to
doubt, and BAND_MEASUREMENTS, figures measured once and transcribed.
"""

import csv
import html
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "assets" / "files" / "software"
LOWDOM = BASE / "260115-002-lowdom"
BIRDID = BASE / "260115-002-birdidpv"
BIRDID_REFS = BIRDID / "reference-recordings"

# Species whose detections the report asks the reader to distrust.
#
# Ruddy Shelduck is in this set on the strongest evidence available anywhere in
# this report: the recordist identified its 01:41:05 frame as his guide calling
# to him across the lake. It briefly left this set when the spectrogram was read
# as a bird call, which is exactly the mistake the report now documents.
SUSPECT = {
    "Botaurus stellaris",
    "Fulica atra",
    "Anser anser",
    "Tadorna tadorna",
    "Tadorna ferruginea",
    "Anas platyrhynchos",
    "Mareca penelope",
    "Ardea cinerea",
    "Numenius arquata",
}

BAND_MEASUREMENTS = [
    ("Red-billed Chough", "24%", "55%", "21%", "−44.3"),
    ("Large-billed Crow", "14%", "85%", "1%", "−41.2"),
    ("Great Bittern", "45%", "49%", "5%", "−51.8"),
    ("Ruddy Shelduck", "52%", "45%", "3%", "−47.2"),
    ("Eurasian Coot", "89%", "10%", "1%", "−48.3"),
]


# BirdNET's models are CC BY-NC-SA 4.0, so this credit is a licence condition
# rather than a courtesy. It is kept in step with the toolkit's own wording.
BIRDNET_CREDIT = """  <p class="report-credit">Identification by
  <a href="https://birdnet.cornell.edu/">BirdNET</a>, developed by the K. Lisa
  Yang Center for Conservation Bioacoustics at the Cornell Lab of Ornithology
  with Chemnitz University of Technology, reached through
  <a href="https://github.com/joeweiss/birdnetlib">birdnetlib</a>. The BirdNET
  models are licensed
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>
  and that non-commercial condition applies to these results. Cite: Kahl, S.,
  Wood, C. M., Eibl, M., &amp; Klinck, H. (2021). BirdNET: A deep learning
  solution for avian diversity monitoring. <em>Ecological Informatics</em>, 61,
  101236. Neither this report nor field-audio-tools is affiliated with or
  endorsed by the BirdNET team.</p>"""


def chrome() -> tuple[str, str]:
    """Return the markup before and after the report <main>.

    The tail carries lowdom's own inline timeline script, including its
    embedded window data. That belongs to lowdom, so it is dropped here and
    each birdidpv page appends its own.
    """
    source = (LOWDOM / "report.html").read_text(encoding="utf-8")
    head_marker = '  <div class="page lowdom-page">'
    tail_marker = "    </main>"
    head = source[: source.index(head_marker)]
    tail = source[source.index(tail_marker) + len(tail_marker) :]

    script_start = tail.index("  <script>")
    script_end = tail.index("  </script>", script_start) + len("  </script>\n")
    dropped = tail[script_start:script_end]
    if "const rows" not in dropped:
        raise SystemExit("Unexpected chrome layout: lowdom's timeline script moved")
    tail = tail[:script_start] + tail[script_end:]
    if "const rows" in tail:
        raise SystemExit("Unexpected chrome layout: lowdom data still present")
    return head, tail


def read_detections() -> list[dict]:
    with (BIRDID / "detections.csv").open(newline="", encoding="utf-8") as handle:
        return [
            {
                "s": float(row["start_seconds"]),
                "e": float(row["end_seconds"]),
                "n": row["common_name"],
                "t": row["scientific_name"],
                "c": float(row["confidence"]),
            }
            for row in csv.DictReader(handle)
        ]


def read_species() -> list[dict]:
    with (BIRDID / "species.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_ranges() -> list[list[float]]:
    with (LOWDOM / "candidate-clean-intervals.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        return [
            [float(row["start_seconds"]), float(row["end_seconds"])]
            for row in csv.DictReader(handle)
        ]


def embedded(detections, ranges, duration, spectrograms=None) -> str:
    spectrograms = spectrograms or {}
    items = []
    for d in detections:
        entry = {
            "s": round(d["s"], 3),
            "e": round(d["e"], 3),
            "n": d["n"],
            "t": d["t"],
            "c": round(d["c"], 4),
        }
        # The file name travels with the detection, so the page never has to
        # rebuild it from a naming convention.
        name = spectrograms.get(round(d["s"] * 1000))
        if name:
            entry["g"] = name
        items.append(entry)
    payload = {"duration": duration, "ranges": ranges, "detections": items}
    return json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")


def metadata_list(summary) -> str:
    p = summary["parameters"]
    rows = [
        ("Sources", "260115_002_Tr1.WAV (track 1 only)"),
        ("Recordist", "Gewenxin Yu"),
        (
            "Recording setup",
            "Two Primo EM273 omni-directional microphones (−37 dB ± 3 dB "
            "at 1 kHz, 80 dB S/N ratio, 60 Hz ~ 20 kHz) and a Zoom F3 recorder",
        ),
        ("Model", "BirdNET (Cornell Lab / Chemnitz UT) via birdnetlib, 3-second frames"),
        (
            "Ranges analysed",
            f'{summary["analysed_range_count"]} below-threshold ranges from lowdom '
            f'· {summary["analysed_timecode"][:8]} of '
            f'{summary["duration_timecode"][:8]} '
            f'({summary["analysed_percent"]:.1f}% of the take)',
        ),
        (
            "Species filter",
            f'{p["latitude"]}°N, {p["longitude"]}°E · week '
            f'{p["week_48"]} of 48 · 6,522 species reduced to 788',
        ),
        ("Minimum confidence", f'{p["min_confidence"]}'),
        (
            "Detections",
            f'{summary["detection_count"]} frames in '
            f'{summary["species_count"]} species',
        ),
    ]
    return "\n".join(
        f"    <dt>{html.escape(key)}</dt><dd>{value}</dd>" for key, value in rows
    )


def read_spectrograms() -> dict[int, str]:
    """Map detection start time in milliseconds to its rendered image."""
    directory = BIRDID / "detection-spectrograms"
    if not directory.is_dir():
        return {}
    index = {}
    for path in sorted(directory.glob("frame-*.webp")):
        index[int(path.stem.split("-")[1])] = path.name
    return index


def read_photos() -> dict[str, dict]:
    path = BIRDID / "species-photos" / "credits.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {p["scientific_name"]: p for p in payload["photos"]}


def read_reference_recordings() -> list[dict]:
    """The Bittern comparison recordings, stored in the package."""
    path = BIRDID_REFS / "credits.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["recordings"]


def reference_players() -> str:
    """Native players, no third-party embed. Credit sits with each one."""
    recordings = read_reference_recordings()
    if not recordings:
        return ""
    items = []
    for r in recordings:
        licence = r["license"].rstrip("/").rsplit("/", 2)[-2].upper()
        country = (r.get("location") or "").split(",")[-1].strip()
        image = r.get("spectrogram")
        picture = (
            f'      <img src="reference-recordings/{html.escape(image, quote=True)}"'
            f' alt="Spectrogram of xeno-canto recording {r["id"]}"'
            ' loading="lazy" decoding="async">\n'
            if image
            else ""
        )
        items.append(
            '    <li class="reference-recording">\n'
            + picture
            + '      <audio controls preload="none" '
            f'src="reference-recordings/{html.escape(r["file_name"], quote=True)}">'
            "</audio>\n"
            '      <span class="reference-recording__credit">'
            f'<a href="{html.escape(r["page"], quote=True)}">XC{r["id"]}</a> · '
            f'{html.escape(r["recordist"] or "unknown")} · '
            f"{html.escape(country)} · CC {html.escape(licence)}</span>\n"
            "    </li>"
        )
    return (
        '  <ul class="reference-recordings">\n'
        + "\n".join(items)
        + "\n  </ul>\n"
        '  <p class="report-explainer">These are stored in this package under '
        "their recordists' CC BY-NC-SA licences rather than embedded from "
        "xeno-canto, so the comparison survives archiving and no reader's "
        "address is disclosed to make it. The spectrograms are re-rendered here "
        "with the same axes and scaling as the detection frames above. "
        "xeno-canto draws its own on a linear frequency axis, which suits the "
        "wide scrubbing strip in its player but leaves the boom as a thin line "
        "along the bottom while the background birds fill the frame. Put next "
        "to a detection from this take, the same sound would look like a "
        "different one.</p>"
    )


def read_taxon_ids() -> list[dict]:
    path = BIRDID / "taxon-ids.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["species"]


def taxon_id_table() -> str:
    """Where each species lives in the other databases."""
    species = read_taxon_ids()
    if not species:
        return ""
    rows = []
    for item in species:
        links = " ".join(
            f'<a href="{html.escape(l["url"], quote=True)}">{html.escape(l["label"])}</a>'
            for l in item["links"]
        )
        rows.append(
            "      <tr><td>"
            f'{html.escape(item.get("common_name") or item["scientific_name"])}'
            f'<span class="scientific">{html.escape(item["scientific_name"])}</span>'
            f'</td><td class="taxon-ids__links">{links}</td></tr>'
        )
    return (
        '  <h2 id="taxon-identifiers">Taxon identifiers</h2>\n'
        '  <p class="report-explainer">The same eleven species in the databases a '
        "detection usually has to travel to. Matched on iNaturalist taxon ID, not "
        "on name — a name search returns a congener often enough that an "
        "identifier attached to the wrong bird is a real risk. Wikidata holds "
        "dozens more per species; those are kept in "
        '<a href="taxon-ids.json">taxon-ids.json</a>.</p>\n'
        '  <table class="species-table taxon-ids">\n'
        "    <thead><tr><th>Species</th><th>Elsewhere</th></tr></thead>\n"
        "    <tbody>\n" + "\n".join(rows) + "\n    </tbody>\n  </table>\n"
    )


def photo_cell(scientific: str, photos: dict[str, dict]) -> str:
    """Thumbnail plus the credit each photographer's licence requires."""
    photo = photos.get(scientific)
    if photo is None:
        return (
            '<td class="species-photo">'
            '<span class="species-photo__none">no photograph</span></td>'
        )
    src = html.escape(f"species-photos/{photo['file_name']}", quote=True)
    who = html.escape(photo.get("photographer") or "unknown photographer")
    code = html.escape(photo["license_code"].upper())
    href = html.escape(photo["taxon_url"], quote=True)
    # Aspect ratios differ per photograph, so the box is sized in CSS with
    # object-fit rather than by hardcoded width/height attributes.
    return (
        f'<td class="species-photo">'
        f'<a href="{href}" rel="noopener noreferrer" target="_blank">'
        f'<img src="{src}" alt="Reference photograph of '
        f'{html.escape(scientific, quote=True)}" loading="lazy" decoding="async"></a>'
        f'<span class="species-photo__credit">{who} · {code}</span></td>'
    )


def species_table(species, interactive: bool, photos: dict[str, dict]) -> str:
    lines = [
        '  <table class="species-table">',
        '    <thead><tr><th class="species-photo-head">Reference</th>'
        '<th>Species</th><th class="numeric">Frames</th>'
        '<th class="numeric">Highest</th><th>At</th><th>First heard</th></tr></thead>',
        "    <tbody>",
    ]
    for row in species:
        scientific = row["scientific_name"]
        attributes = (
            f' class="species-row" data-species="{html.escape(scientific, quote=True)}"'
            ' tabindex="0" role="button"'
            if interactive
            else ""
        )
        note = (
            '<span class="flagged-note">check by ear</span>'
            if scientific in SUSPECT
            else ""
        )
        lines.append(
            f"      <tr{attributes}>"
            f"{photo_cell(scientific, photos)}"
            f'<td>{html.escape(row["common_name"])}'
            f'<span class="scientific">{html.escape(scientific)}</span>'
            f"{note}</td>"
            f'<td class="numeric">{row["detection_count"]}</td>'
            f'<td class="numeric">{float(row["max_confidence"]):.3f}</td>'
            f'<td>{html.escape(row["max_confidence_timecode"][:8])}</td>'
            f'<td>{html.escape(row["first_start_timecode"][:8])}</td>'
            "</tr>"
        )
    lines.extend(["    </tbody>", "  </table>"])
    lines.append(PHOTO_NOTE)
    return "\n".join(lines)


PHOTO_NOTE = """  <p class="report-explainer">Reference photographs come from
  <a href="https://www.inaturalist.org/">iNaturalist</a> and are stored in this
  package rather than hot-linked, so it survives being archived and no reader's
  address is disclosed to a third party. Each file is kept exactly as
  iNaturalist served it and remains under its photographer's licence, credited
  beside it; the machine-readable record is in
  <a href="species-photos/credits.json">credits.json</a>. A photograph shows
  what the species looks like. It is not evidence that the species was here —
  nine of these eleven are the rows we are asking you to doubt, and one of those
  nine is a photograph of a bird that was never there.</p>"""


def band_table() -> str:
    lines = [
        '  <table class="band-table">',
        "    <thead><tr><th>Detected as</th><th>150–400 Hz</th>"
        "<th>400 Hz–2 kHz</th><th>2–8 kHz</th><th>Level</th></tr></thead>",
        "    <tbody>",
    ]
    for name, low, mid, high, level in BAND_MEASUREMENTS:
        lines.append(
            f"      <tr><td>{html.escape(name)}</td><td>{low}</td><td>{mid}</td>"
            f"<td>{high}</td><td>{level} dBFS</td></tr>"
        )
    lines.extend(["    </tbody>", "  </table>"])
    return "\n".join(lines)


NOTICE = """  <p class="notice"><strong>Machine identification, not a verified
  record:</strong> BirdNET scores each 3-second frame; it does not confirm that a
  species was present. Confidence is not a probability, and a high score on one
  frame is not a record. Listen before citing any of this.</p>"""

READING = """  <h2>Reading this against a frozen lake</h2>
  <p class="report-explainer">Two corvids account for 99 of the 128 detections and
  behave like real calls: they carry energy well above 2 kHz and sit 3–11 dB above
  everything else. The other nine species are all deep-voiced waterbirds, on a lake
  that had frozen over by mid-January at 4,055 m. Measuring the detected frames
  after a 150 Hz high-pass shows where the two groups part:</p>
{band_table}
  <p class="report-explainer">The waterbird detections concentrate their energy
  below 400 Hz at a lower level, and mostly show none of the high-frequency
  structure the corvid detections do. That is the band the ice resonance occupies —
  the sound the local guides call <em>long hou</em>, “dragon roar”. A plausible
  reading is that BirdNET is mapping ice onto the birds whose calls are booms, and
  <a href="https://xeno-canto.org/species/Botaurus-stellaris">Great Bittern</a> at
  0.906 is the clearest case: its twelve detections arrive in sustained runs,
  eight of them inside seventy seconds, and not one of their spectrograms shows a
  call above the ice.</p>
  <p class="report-explainer">Listening to the species explains the mistake
  rather than excusing it. On the first page of xeno-canto recordings for
  <em>Botaurus stellaris</em> — <a href="https://xeno-canto.org/891071">XC891071</a>,
  <a href="https://xeno-canto.org/1000766">XC1000766</a>,
  <a href="https://xeno-canto.org/832807">XC832807</a> and
  <a href="https://xeno-canto.org/741523">XC741523</a> among them — the booms
  really are close to the dragon roar. Close enough that the confusion looks
  reasonable rather than absurd. Listen to them here, then to any green stretch
  of the timeline above:</p>
{reference_players}
  <p class="report-explainer">One thing separates them by ear: the ice carries an
  electronic quality that the bird does not. That difference is the interesting
  part of the error, it is plainly audible, and none of the spectrogram
  statistics on this page found it.</p>
  <p class="report-explainer">Ice is not the only thing here that is not a bird.
  The frame at 01:41:05, which BirdNET calls Ruddy Shelduck at 0.928 — the second
  highest confidence in the whole run — is a person. It is Xiao Zhang, one of the
  guides, calling across the lake to the recordist, who identified it on
  listening. There is no bird in those three seconds at all.</p>
  <p class="report-explainer">That frame is worth opening, because it also shows
  how a spectrogram can be misread. It does carry harmonic stacks between 1 and
  3 kHz, and we first took them for a call: ice does not produce structure like
  that, so we moved the species out of the doubtful list. But a voice does. Those
  are a pitch contour gliding through its harmonics, formants around 1.2 and
  2 kHz, and four or five syllables in the last second — speech, not song. The
  band average in the table above had hidden it under the low-frequency bed, and
  the picture that uncovered it was then read wrong. Only listening settled it.</p>
  <p class="report-explainer">So the ledger runs three ways, not two: real calls,
  lake ice, and at least one human voice. Every row marked
  <span class="flagged-note">check by ear</span> is one we would not cite without
  going back to the source WAV — and the loudest argument for that rule is that
  the model's second most confident bird in three hours was a man shouting.</p>"""


def build_data_report(summary, detections, species, ranges, photos) -> str:
    head, tail = chrome()
    duration = summary["duration_seconds"]
    return f"""{head}  <div class="page birdidpv-page">
    <main class="birdidpv-report">
      <div class="report-breadcrumb"><a href="/software">Software</a> / field-audio-tools / birdidpv-report-and-analysis</div>
      <h1>birdidpv identification report</h1>
{NOTICE}
  <dl>
{metadata_list(summary)}
  </dl>
  <canvas id="timeline" width="1400" height="320"
    aria-label="Timeline of BirdNET detections inside the ranges lowdom left unflagged"></canvas>
  <div class="report-legend">
    <span><i class="report-swatch report-swatch--range"></i>range analysed</span>
    <span><i class="report-swatch report-swatch--strong"></i>high confidence</span>
    <span><i class="report-swatch report-swatch--weak"></i>low confidence</span>
  </div>
  <p class="report-explainer">The pale band marks the {summary["analysed_range_count"]}
  ranges lowdom left below its threshold; the rest of the take was not analysed. Each
  mark is one 3-second detection, taller and darker with higher confidence.</p>
  <h2>Species</h2>
{species_table(species, False, photos)}
{taxon_id_table()}
{READING.format(band_table=band_table(), reference_players=reference_players())}
  <p class="report-links">
    <a href="report-js.html"><img class="report-link-icon" src="/static/software-output-polished.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the multimedia report</a>
    <a href="report-multimedia-bare.html"><img class="report-link-icon" src="/static/software-output-bare.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the bare CLI multimedia report</a>
    <a href="report-bare.html"><img class="report-link-icon" src="/static/software-output-bare.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the bare CLI timeline report</a>
    <a href="../260115-002-lowdom/report-js.html"><img class="report-link-icon" src="/static/software-output-polished.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the lowdom screening report</a>
    <a href="detections.csv"><img class="report-link-icon" src="/static/software-format-csv.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Download every detection</a>
    <a href="species.csv"><img class="report-link-icon" src="/static/software-format-csv.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Download the species roll-up</a>
    <a href="taxon-ids.json"><img class="report-link-icon" src="/static/software-format-json.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Download the taxon identifiers</a>
    <a href="summary.json"><img class="report-link-icon" src="/static/software-format-json.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Read the summary</a>
  </p>
{BIRDNET_CREDIT}
    </main>{tail.replace("</body>", STATIC_SCRIPT.format(data=embedded(detections, ranges, duration)) + "</body>")}"""


STATIC_SCRIPT = """  <script>
    const data = {data};
    const canvas = document.getElementById('timeline');
    const ctx = canvas.getContext('2d');
    const width = canvas.width, height = canvas.height;
    const scale = seconds => seconds * width / data.duration;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#dfeee7';
    data.ranges.forEach(range => {{
      const x = scale(range[0]);
      ctx.fillRect(x, 0, Math.max(1, scale(range[1]) - x), height);
    }});
    data.detections.forEach(det => {{
      const x = scale(det.s);
      const bar = Math.max(4, det.c * height);
      ctx.fillStyle = `rgba(20, 78, 58, ${{0.25 + 0.75 * det.c}})`;
      ctx.fillRect(x, height - bar, Math.max(2, scale(det.e) - x), bar);
    }});
  </script>
"""


def build_multimedia_report(
    summary, detections, species, ranges, photos, spectrograms
) -> str:
    head, tail = chrome()
    first_spectrogram = next(
        (
            spectrograms[key]
            for key in (round(d["s"] * 1000) for d in detections)
            if key in spectrograms
        ),
        "",
    )
    duration = summary["duration_seconds"]
    body = f"""{head}  <div class="page birdidpv-page">
    <main class="birdidpv-report">
      <div class="report-breadcrumb"><a href="/software">Software</a> / field-audio-tools / birdidpv-report-and-analysis</div>
      <h1>birdidpv multimedia identification report</h1>
{NOTICE}
  <dl>
{metadata_list(summary)}
  </dl>

  <div class="report-controls">
    <button id="enable" type="button" aria-pressed="false">Enable hover playback</button>
    <button id="clear" type="button">Show all species</button>
    <p id="status" class="status" role="status">Audio is off. Enable it once, then hover over the timeline.</p>
    <audio id="audio" controls preload="metadata"
      src="../260115-002-lowdom/recording-preview-48k/segment-000.ogg"></audio>
  </div>

  <canvas id="timeline" width="1400" height="320" tabindex="0"
    aria-label="Interactive timeline of BirdNET detections. Enable audio, then move over a detection to hear its three seconds."></canvas>
  <div class="report-legend">
    <span><i class="report-swatch report-swatch--range"></i>range analysed</span>
    <span><i class="report-swatch report-swatch--strong"></i>high confidence</span>
    <span><i class="report-swatch report-swatch--weak"></i>low confidence</span>
  </div>
  <figure id="spectrogram-panel">
    <img id="spectrogram" src="detection-spectrograms/{first_spectrogram}"
      alt="Spectrogram of the selected detection frame" decoding="async">
    <figcaption id="spectrogram-caption">Select a detection to see the spectrogram
      of its three seconds.</figcaption>
  </figure>
  <p class="report-explainer">The pale band marks the {summary["analysed_range_count"]}
  ranges lowdom left below its threshold. Hover to select the nearest detection;
  playback starts after a short pause and stops at the end of that frame. Click to
  play immediately, which also copies the start timecode; the locked detection
  keeps an orange marker so you can see where playback sits after the pointer
  moves on. Select a species below to show only its detections. The spectrogram
  above is rendered ahead of time from the source WAV, not from the preview, on a
  logarithmic frequency axis so the sub-400 Hz band stays readable: a real call
  shows harmonic structure in the kilohertz bands, while broadband energy low down
  with nothing above it is geophony whatever the model named it. The preview audio
  is the same lossy 48 kbit/s Opus derivative the lowdom report uses; use the
  source WAV files for verification.</p>
  <h2>Species</h2>
  <p class="report-explainer">Select a row to filter the timeline.</p>
{species_table(species, True, photos)}
{taxon_id_table()}
{READING.format(band_table=band_table(), reference_players=reference_players())}
  <p class="report-links">
    <a href="report.html"><img class="report-link-icon" src="/static/software-output-polished.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the site data report</a>
    <a href="report-multimedia-bare.html"><img class="report-link-icon" src="/static/software-output-bare.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the bare CLI multimedia report</a>
    <a href="report-bare.html"><img class="report-link-icon" src="/static/software-output-bare.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the bare CLI timeline report</a>
    <a href="../260115-002-lowdom/report-js.html"><img class="report-link-icon" src="/static/software-output-polished.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Open the lowdom screening report</a>
    <a href="detections.csv"><img class="report-link-icon" src="/static/software-format-csv.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Download every detection</a>
    <a href="species.csv"><img class="report-link-icon" src="/static/software-format-csv.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Download the species roll-up</a>
    <a href="taxon-ids.json"><img class="report-link-icon" src="/static/software-format-json.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Download the taxon identifiers</a>
    <a href="summary.json"><img class="report-link-icon" src="/static/software-format-json.svg" alt="" width="16" height="16" decoding="async" aria-hidden="true">Read the summary</a>
  </p>
{BIRDNET_CREDIT}
    </main>"""
    script = INTERACTIVE_SCRIPT.replace(
        "__DATA__", embedded(detections, ranges, duration, spectrograms)
    )
    return body + tail.replace("</body>", script + "</body>")


INTERACTIVE_SCRIPT = """  <script>
    const data = __DATA__;
    const chunkSeconds = 300;
    const previewDir = '../260115-002-lowdom/recording-preview-48k';
    const spectrogramDir = 'detection-spectrograms';
    // Matches the orange lowdom uses for flagged windows.
    const LOCKED_COLOUR = '#d85b00';
    const canvas = document.getElementById('timeline');
    const ctx = canvas.getContext('2d');
    const spectrogram = document.getElementById('spectrogram');
    const spectrogramCaption = document.getElementById('spectrogram-caption');
    const audio = document.getElementById('audio');
    const enableButton = document.getElementById('enable');
    const clearButton = document.getElementById('clear');
    const status = document.getElementById('status');
    const rows = Array.from(document.querySelectorAll('tr.species-row'));
    let enabled = false;
    let filter = null;
    let hoverIndex = -1;
    let playingIndex = -1;
    let playingEnd = 0;
    let loadedChunk = 0;
    let hoverTimer = 0;
    let playRequest = 0;

    function timecode(seconds) {
      const whole = Math.floor(seconds);
      const hours = Math.floor(whole / 3600);
      const minutes = Math.floor((whole % 3600) / 60);
      const secs = whole % 60;
      return [hours, minutes, secs].map(value => String(value).padStart(2, '0')).join(':');
    }

    function visible() {
      const result = [];
      data.detections.forEach((det, index) => {
        if (filter === null || det.t === filter) result.push(index);
      });
      return result;
    }

    function scale(seconds) {
      return seconds * canvas.width / data.duration;
    }

    function describe(index, prefix) {
      const det = data.detections[index];
      status.textContent = `${prefix}${timecode(det.s)} · ${det.n} · confidence ${det.c.toFixed(3)}`;
      showSpectrogram(index);
    }

    // Every frame was rendered ahead of time, so switching is just an src swap.
    function showSpectrogram(index) {
      if (!spectrogram) return;
      const det = data.detections[index];
      if (!det || !det.g) {
        spectrogramCaption.textContent = 'No spectrogram was rendered for this frame.';
        return;
      }
      spectrogram.src = `${spectrogramDir}/${det.g}`;
      spectrogram.alt = `Spectrogram of the frame at ${timecode(det.s)}, detected as ${det.n}`;
      spectrogramCaption.textContent =
        `${timecode(det.s)}–${timecode(det.e)} · ${det.n} · confidence ${det.c.toFixed(3)}`;
    }

    function draw() {
      const width = canvas.width;
      const height = canvas.height;
      const shown = new Set(visible());
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#dfeee7';
      data.ranges.forEach(range => {
        const x = scale(range[0]);
        ctx.fillRect(x, 0, Math.max(1, scale(range[1]) - x), height);
      });
      data.detections.forEach((det, index) => {
        if (!shown.has(index)) return;
        const x = scale(det.s);
        const bar = Math.max(4, det.c * height);
        const w = Math.max(2, scale(det.e) - x);
        ctx.fillStyle = index === playingIndex
          ? '#000000'
          : `rgba(20, 78, 58, ${0.25 + 0.75 * det.c})`;
        ctx.fillRect(x, height - bar, w, bar);
      });
      // The locked detection keeps an orange marker of its own, so it stays
      // visible after the pointer moves on. Hover stays black.
      if (playingIndex >= 0 && shown.has(playingIndex)) {
        marker(scale(data.detections[playingIndex].s), LOCKED_COLOUR, 3);
      }
      if (hoverIndex >= 0 && hoverIndex !== playingIndex && shown.has(hoverIndex)) {
        marker(scale(data.detections[hoverIndex].s), '#000', 2);
      }
    }

    function marker(x, colour, lineWidth) {
      ctx.strokeStyle = colour;
      ctx.lineWidth = lineWidth;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }

    function nearestAt(clientX) {
      const candidates = visible();
      if (!candidates.length) return -1;
      const rect = canvas.getBoundingClientRect();
      const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
      const seconds = ratio * data.duration;
      let best = candidates[0];
      let bestDistance = Infinity;
      candidates.forEach(index => {
        const det = data.detections[index];
        const distance = seconds < det.s
          ? det.s - seconds
          : (seconds > det.e ? seconds - det.e : 0);
        if (distance < bestDistance) {
          bestDistance = distance;
          best = index;
        }
      });
      return best;
    }

    async function copyTextToClipboard(text) {
      if (navigator.clipboard && window.isSecureContext) {
        try {
          await navigator.clipboard.writeText(text);
          return true;
        } catch (error) {
          return false;
        }
      }
      const area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.left = '-9999px';
      document.body.appendChild(area);
      area.select();
      let copied = false;
      try {
        copied = document.execCommand('copy');
      } catch (error) {
        copied = false;
      }
      document.body.removeChild(area);
      return copied;
    }

    async function playDetection(index, options = {}) {
      const force = options.force === true;
      const request = ++playRequest;
      if (index < 0) return;
      if (!enabled && !force) {
        describe(index, 'Audio is off · ');
        return;
      }
      const det = data.detections[index];
      try {
        if (!enabled && force) {
          audio.muted = true;
          await audio.play();
          audio.pause();
          audio.muted = false;
        }
        const chunk = Math.floor(det.s / chunkSeconds);
        const localStart = det.s - chunk * chunkSeconds;
        if (chunk !== loadedChunk) {
          audio.pause();
          loadedChunk = chunk;
          audio.src = `${previewDir}/segment-${String(chunk).padStart(3, '0')}.ogg`;
          audio.load();
          if (audio.readyState < 1) {
            await new Promise((resolve, reject) => {
              const ready = () => {
                audio.removeEventListener('error', failed);
                resolve();
              };
              const failed = () => {
                audio.removeEventListener('loadedmetadata', ready);
                reject(new Error('Audio chunk could not be loaded'));
              };
              audio.addEventListener('loadedmetadata', ready, { once: true });
              audio.addEventListener('error', failed, { once: true });
            });
          }
        }
        if (request !== playRequest) return;
        playingIndex = index;
        playingEnd = localStart + (det.e - det.s);
        draw();
        audio.currentTime = localStart;
        await audio.play();
        const copied = await copyTextToClipboard(timecode(det.s));
        describe(index, copied ? 'Playing · copied · ' : 'Playing · ');
      } catch (error) {
        playingIndex = -1;
        draw();
        if (enabled) setHoverPlayback(false);
        status.textContent = 'Playback was blocked. Click Enable hover playback and try again.';
      }
    }

    function setHoverPlayback(on) {
      enabled = on;
      enableButton.textContent = on ? 'Disable hover playback' : 'Enable hover playback';
      enableButton.setAttribute('aria-pressed', on ? 'true' : 'false');
      if (!on) clearTimeout(hoverTimer);
    }

    async function toggleHoverPlayback() {
      if (enabled) {
        setHoverPlayback(false);
        status.textContent = 'Hover playback off. Click a detection to play without hover.';
        return;
      }
      try {
        audio.muted = true;
        await audio.play();
        audio.pause();
        audio.muted = false;
        setHoverPlayback(true);
        status.textContent = 'Ready. Hover over the timeline or click a detection.';
      } catch (error) {
        audio.muted = false;
        status.textContent = 'The browser could not enable playback. Use the audio controls once, then try again.';
      }
    }

    function setFilter(species) {
      filter = species;
      hoverIndex = -1;
      rows.forEach(row => {
        row.classList.toggle('selected', species !== null && row.dataset.species === species);
      });
      draw();
      if (species === null) {
        status.textContent = `Showing all ${data.detections.length} detections.`;
      } else {
        const count = visible().length;
        const name = data.detections.find(det => det.t === species).n;
        status.textContent = `Showing ${count} detection${count === 1 ? '' : 's'} of ${name}.`;
      }
    }

    enableButton.addEventListener('click', toggleHoverPlayback);
    clearButton.addEventListener('click', () => setFilter(null));
    rows.forEach(row => {
      const select = () => setFilter(
        filter === row.dataset.species ? null : row.dataset.species
      );
      // The photograph links out to iNaturalist. Without this the same click
      // would also toggle the row filter on the way up.
      row.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', event => event.stopPropagation());
      });
      row.addEventListener('click', select);
      row.addEventListener('keydown', event => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        select();
      });
    });
    audio.addEventListener('timeupdate', () => {
      if (playingIndex >= 0 && audio.currentTime >= playingEnd) {
        audio.pause();
        describe(playingIndex, 'Finished · ');
        playingIndex = -1;
        draw();
      }
    });
    canvas.addEventListener('pointermove', event => {
      const index = nearestAt(event.clientX);
      if (index === hoverIndex || index < 0) return;
      hoverIndex = index;
      draw();
      describe(index, enabled ? 'Selected · ' : 'Audio is off · ');
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => playDetection(index), 180);
    });
    canvas.addEventListener('pointerleave', () => clearTimeout(hoverTimer));
    canvas.addEventListener('pointerdown', event => {
      clearTimeout(hoverTimer);
      hoverIndex = nearestAt(event.clientX);
      draw();
      playDetection(hoverIndex, { force: true });
    });
    canvas.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Enter', ' '].includes(event.key)) return;
      event.preventDefault();
      const candidates = visible();
      if (!candidates.length) return;
      let position = candidates.indexOf(hoverIndex);
      if (position < 0) position = 0;
      else if (event.key === 'ArrowLeft') position = Math.max(0, position - 1);
      else if (event.key === 'ArrowRight') position = Math.min(candidates.length - 1, position + 1);
      hoverIndex = candidates[position];
      draw();
      describe(hoverIndex, 'Selected · ');
      if (event.key === 'Enter' || event.key === ' ') {
        playDetection(hoverIndex, { force: true });
      }
    });
    draw();
  </script>
"""


def main() -> None:
    summary = json.loads((BIRDID / "summary.json").read_text(encoding="utf-8"))
    detections = read_detections()
    species = read_species()
    ranges = read_ranges()

    photos = read_photos()
    spectrograms = read_spectrograms()

    (BIRDID / "report.html").write_text(
        build_data_report(summary, detections, species, ranges, photos),
        encoding="utf-8",
    )
    (BIRDID / "report-js.html").write_text(
        build_multimedia_report(
            summary, detections, species, ranges, photos, spectrograms
        ),
        encoding="utf-8",
    )
    print(
        f"wrote report.html and report-js.html "
        f"({len(detections)} detections, {len(photos)} photographs, "
        f"{len(spectrograms)} spectrograms)"
    )


if __name__ == "__main__":
    main()
