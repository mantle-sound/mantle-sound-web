#!/usr/bin/env python3
"""Rebuild the Take 002 birdidpv demonstration package.

The package under assets/files/software/260115-002-birdidpv is entirely derived.
Nothing in it is hand-edited, and this script is the definition of how it is
produced. Run it in stages, because they cost very different amounts:

  analyse   Run birdidpv over the ranges lowdom left unflagged. Slow — BirdNET
            takes minutes — and needs the source WAV, which lives on removable
            media. Rewrites the CSVs, the photographs, and the spectrograms.
  render    Re-render the two bare CLI reports from data already in the package.
            Seconds, no source audio. This is what a change to report markup or
            wording needs.
  site      Rebuild the site-styled report.html and report-js.html.
  check     Regenerate everything cheap in memory and fail if the files on disk
            differ. Proves the package still matches its inputs.

Default is `render site`, the cheap pair, since that is what almost every edit
needs. Pass `all` to include the analysis.

    python3 tools/build_birdidpv_package.py            # render + site
    python3 tools/build_birdidpv_package.py check
    python3 tools/build_birdidpv_package.py all --source /path/to/Tr1.WAV

The CLI writes report.html and report-multimedia.html. The site needs those
names for its own styled pages, so the bare pair is renamed on the way in. That
convention is documented in the toolkit README; it is applied here, not there,
because it is a property of this site rather than of the tool.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOFTWARE = REPO / "assets" / "files" / "software"
PACKAGE = SOFTWARE / "260115-002-birdidpv"
LOWDOM = SOFTWARE / "260115-002-lowdom"

DEFAULT_SOURCE = Path("/run/media/xeanon/4A21-0000/260115_002_Tr1.WAV")

# The parameters of the published run. Changing one of these means the package
# has to be rebuilt with `all`, not `render`.
RUN = {
    "lat": "29.898",
    "lon": "102.030",
    "week": "3",
    "min_conf": "0.25",
    "photo_size": "medium",
    "spectrogram_size": "560x260",
    "spectrogram_format": "webp",
}

# Relative paths the report points at. The preview segments belong to the lowdom
# package: 62 MB of Opus that would be pointless to duplicate.
PREVIEW_DIR = "../260115-002-lowdom/recording-preview-48k"
PREVIEW_CHUNK_SECONDS = 300.0
LOWDOM_REPORT = "../260115-002-lowdom/report-js.html"
PHOTO_DIR = "species-photos"
SPECTROGRAM_DIR = "detection-spectrograms"

# The CLI calls these report.html and report-multimedia.html. The site needs
# those two names for its own styled pages, so the bare pair is kept under a
# suffix. This is a property of this site, not of the tool.
BARE_REPORTS = ("report-bare.html", "report-multimedia-bare.html")


def _toolkit_import():
    """Import the toolkit, whether installed or sitting beside this checkout."""
    try:
        import field_audio_tools  # noqa: F401
    except ImportError:
        for candidate in (
            REPO.parent / "field-audio-tools" / "src",
            Path("/run/media/xeanon/T9/archives/_FOSS-mantle-sound")
            / "field-audio-tools"
            / "src",
        ):
            if candidate.is_dir():
                sys.path.insert(0, str(candidate))
                break
        else:
            raise SystemExit(
                "field-audio-tools is not importable. Install it, or place a "
                "checkout beside this repository."
            )


def load_package_data():
    """Everything the reports are rendered from, read back out of the package."""
    _toolkit_import()
    from field_audio_tools.birdidpv import (
        Detection,
        read_intervals_csv,
        summarize_species,
    )
    from field_audio_tools.inaturalist import SpeciesPhoto

    with (PACKAGE / "detections.csv").open(newline="", encoding="utf-8") as handle:
        detections = [
            Detection(
                start_seconds=float(row["start_seconds"]),
                end_seconds=float(row["end_seconds"]),
                scientific_name=row["scientific_name"],
                common_name=row["common_name"],
                confidence=float(row["confidence"]),
                track=int(row["track"]),
            )
            for row in csv.DictReader(handle)
        ]

    credits_path = PACKAGE / PHOTO_DIR / "credits.json"
    photos = {}
    if credits_path.exists():
        payload = json.loads(credits_path.read_text(encoding="utf-8"))
        photos = {p["scientific_name"]: SpeciesPhoto(**p) for p in payload["photos"]}

    taxon_path = PACKAGE / "taxon-ids.json"
    taxon_ids = []
    if taxon_path.exists():
        from field_audio_tools.taxonids import TaxonIdentifiers

        for entry in json.loads(taxon_path.read_text(encoding="utf-8"))["species"]:
            taxon_ids.append(
                TaxonIdentifiers(
                    scientific_name=entry["scientific_name"],
                    common_name=entry.get("common_name"),
                    inaturalist_id=entry["inaturalist_id"],
                    wikidata_id=entry["wikidata_id"],
                    identifiers=entry["identifiers"],
                )
            )

    spectrograms = {
        int(path.stem.split("-")[1]): path.name
        for path in sorted((PACKAGE / SPECTROGRAM_DIR).glob("frame-*.*"))
    }

    return {
        "summary": json.loads((PACKAGE / "summary.json").read_text(encoding="utf-8")),
        "detections": detections,
        "species": summarize_species(detections),
        "intervals": read_intervals_csv(LOWDOM / "candidate-clean-intervals.csv"),
        "photos": photos,
        "spectrograms": spectrograms,
        "taxon_ids": taxon_ids,
    }


def preview_available() -> bool:
    """The multimedia report borrows lowdom's preview rather than duplicating it."""
    _toolkit_import()
    from field_audio_tools.preview import has_segments

    return has_segments((PACKAGE / PREVIEW_DIR).resolve())


def render_bare_reports(data) -> dict[str, str]:
    """The exact text the two bare reports should contain."""
    _toolkit_import()
    from field_audio_tools.birdidpv import _report_html, _report_multimedia_html

    return {
        "report-bare.html": _report_html(
            data["summary"],
            data["detections"],
            data["species"],
            data["intervals"],
            data["photos"],
            PHOTO_DIR,
            data["taxon_ids"],
        ),
        "report-multimedia-bare.html": _report_multimedia_html(
            data["summary"],
            data["detections"],
            data["species"],
            data["intervals"],
            preview_dir=PREVIEW_DIR,
            chunk_seconds=PREVIEW_CHUNK_SECONDS,
            bare_report_href="report-bare.html",
            lowdom_report_href=LOWDOM_REPORT,
            photos=data["photos"],
            photo_dir=PHOTO_DIR,
            spectrograms=data["spectrograms"],
            spectrogram_dir=SPECTROGRAM_DIR,
            has_preview=preview_available(),
            taxon_ids=data["taxon_ids"],
        ),
    }


# Bittern reference recordings the report asks the reader to compare by ear.
# All four are CC BY-NC-SA 4.0, the same licence this site carries, so they are
# stored in the package rather than embedded from xeno-canto: an iframe would
# load a third party's player on every view, disclose every reader's address,
# and leave nothing behind when the page is archived.
REFERENCE_DIR = "reference-recordings"
REFERENCE_IDS = (891071, 1000766, 832807, 741523)
XC_API = "https://xeno-canto.org/api/3/recordings"
XC_KEY_FILE = Path.home() / ".config" / "avibase-search" / "config"
ALLOWED_REFERENCE_LICENCES = ("by-nc-sa", "by-sa", "by", "zero", "publicdomain")


def _xc_key(explicit: str | None) -> str:
    if explicit:
        return explicit
    if XC_KEY_FILE.is_file():
        for line in XC_KEY_FILE.read_text().splitlines():
            if line.startswith("XC_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(
        f"No xeno-canto API key. Put XC_API_KEY= in {XC_KEY_FILE}, or pass "
        "--xc-key."
    )


def stage_references(key: str | None) -> None:
    """Fetch the comparison recordings and record who made them."""
    import urllib.parse
    import urllib.request

    key = _xc_key(key)
    target = PACKAGE / REFERENCE_DIR
    target.mkdir(parents=True, exist_ok=True)
    agent = {"User-Agent": "mantle-sound/0.1 (field-audio-tools report)"}
    entries = []
    for number in REFERENCE_IDS:
        query = urllib.parse.urlencode({"query": f"nr:{number}", "key": key})
        request = urllib.request.Request(f"{XC_API}?{query}", headers=agent)
        with urllib.request.urlopen(request, timeout=30) as response:
            results = json.load(response).get("recordings") or []
        if not results:
            raise SystemExit(f"xeno-canto returned nothing for XC{number}")
        item = results[0]
        licence = item.get("lic", "")
        if not any(part in licence for part in ALLOWED_REFERENCE_LICENCES):
            raise SystemExit(
                f"XC{number} is licensed {licence}, which this package will not "
                "redistribute. Link to it instead."
            )
        name = f"xc{number}.mp3"
        if not (target / name).is_file():
            audio = urllib.request.Request(
                f"https://xeno-canto.org/{number}/download", headers=agent
            )
            with urllib.request.urlopen(audio, timeout=120) as response:
                (target / name).write_bytes(response.read())
        # Rendered with the toolkit's own settings, identical to the detection
        # frames elsewhere on the page. xeno-canto publishes its own sonograms,
        # but they use a different frequency axis and scaling, and two pictures
        # drawn to different rules cannot honestly be set side by side.
        _toolkit_import()
        from field_audio_tools.common import require_program
        from field_audio_tools.spectrograms import render_one

        minutes, _, seconds = (item.get("length") or "0:20").partition(":")
        duration = int(minutes) * 60 + int(seconds or 0) + 1
        image = f"xc{number}.webp"
        render_one(
            target / name,
            target / image,
            0.0,
            duration,
            size=RUN["spectrogram_size"],
            ffmpeg=require_program("ffmpeg"),
        )
        entries.append(
            {
                "id": number,
                "file_name": name,
                "spectrogram": image,
                "page": f"https://xeno-canto.org/{number}",
                "scientific_name": f"{item.get('gen')} {item.get('sp')}".strip(),
                "common_name": item.get("en"),
                "type": item.get("type"),
                "length": item.get("length"),
                "quality": item.get("q"),
                "location": f"{item.get('loc')}, {item.get('cnt')}",
                "recordist": item.get("rec"),
                "license": licence,
            }
        )
        print(f"  XC{number}  {item.get('rec')}  {licence.rsplit('/', 3)[-3:][0]}")
    (target / "credits.json").write_text(
        json.dumps(
            {
                "source": "xeno-canto",
                "note": (
                    "Stored in this package under each recordist's CC licence, "
                    "not embedded from xeno-canto. Attribution and share-alike "
                    "terms are the recordists'."
                ),
                "recordings": entries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"  wrote {len(entries)} recordings and spectrograms into "
        f"{REFERENCE_DIR}/"
    )


def resolve_birdidpv(explicit: Path | None) -> str:
    """Find a birdidpv that has the BirdNET extra installed.

    TensorFlow is heavy enough that it usually lives in its own virtualenv
    rather than in whatever interpreter is running this script.
    """
    if explicit:
        if not Path(explicit).is_file():
            raise SystemExit(f"No such birdidpv executable: {explicit}")
        return str(explicit)
    found = shutil.which("birdidpv")
    if found:
        return found
    fallback = Path.home() / ".venvs" / "fat-birdnet" / "bin" / "birdidpv"
    if fallback.is_file():
        return str(fallback)
    raise SystemExit(
        "birdidpv is not on PATH. Install field-audio-tools with the birdnet "
        "extra, or pass --birdidpv /path/to/birdidpv."
    )


def stage_analyse(source: Path, birdidpv: str) -> None:
    if not source.is_file():
        raise SystemExit(
            f"Source audio not found: {source}\n"
            "It lives on removable media; pass --source if it is mounted "
            "elsewhere."
        )
    intervals = LOWDOM / "candidate-clean-intervals.csv"
    if not intervals.is_file():
        raise SystemExit(f"lowdom output missing: {intervals}")

    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch) / "birdidpv"
        command = [
            birdidpv,
            str(source),
            "--intervals",
            str(intervals),
            "--lat",
            RUN["lat"],
            "--lon",
            RUN["lon"],
            "--week",
            RUN["week"],
            "--min-conf",
            RUN["min_conf"],
            "--photos",
            "--photo-dir",
            PHOTO_DIR,
            "--photo-size",
            RUN["photo_size"],
            "--spectrograms",
            "--spectrogram-dir",
            SPECTROGRAM_DIR,
            "--spectrogram-size",
            RUN["spectrogram_size"],
            "--spectrogram-format",
            RUN["spectrogram_format"],
            "--taxon-ids",
            # Data only. The reports are rendered by the render stage, which
            # knows where the package will finally sit and can therefore point
            # at lowdom's preview audio with a relative path that resolves.
            # Asking the CLI for them here would make it generate 62 MB of
            # preview into a temporary directory to satisfy a path that cannot
            # resolve yet.
            "--report",
            "none",
            "--output",
            str(out),
        ]
        print("  running birdidpv (this takes minutes)", flush=True)
        subprocess.run(command, check=True)

        PACKAGE.mkdir(parents=True, exist_ok=True)
        for name in ("detections.csv", "species.csv", "summary.json", "taxon-ids.json"):
            if (out / name).is_file():
                shutil.copy2(out / name, PACKAGE / name)
        for directory in (PHOTO_DIR, SPECTROGRAM_DIR):
            target = PACKAGE / directory
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(out / directory, target)
    print(f"  analysed into {PACKAGE.relative_to(REPO)}")


def stage_render() -> None:
    data = load_package_data()
    for name, text in render_bare_reports(data).items():
        (PACKAGE / name).write_text(text, encoding="utf-8")
    print(f"  wrote {', '.join(BARE_REPORTS)}")


def stage_site() -> None:
    sys.path.insert(0, str(REPO / "tools"))
    import birdidpv_site_pages

    birdidpv_site_pages.main()


def stage_check() -> int:
    """Fail if anything cheap to regenerate has drifted from its inputs."""
    problems = []
    data = load_package_data()

    for name, text in render_bare_reports(data).items():
        path = PACKAGE / name
        if not path.exists():
            problems.append(f"{name} is missing")
        elif path.read_text(encoding="utf-8") != text:
            problems.append(f"{name} differs from what birdidpv would render")

    sys.path.insert(0, str(REPO / "tools"))
    import birdidpv_site_pages

    for name, builder in (
        ("report.html", "build_data_report"),
        ("report-js.html", "build_multimedia_report"),
    ):
        args = (
            data["summary"],
            birdidpv_site_pages.read_detections(),
            birdidpv_site_pages.read_species(),
            birdidpv_site_pages.read_ranges(),
            birdidpv_site_pages.read_photos(),
        )
        if name == "report-js.html":
            args = args + (birdidpv_site_pages.read_spectrograms(),)
        text = getattr(birdidpv_site_pages, builder)(*args)
        path = PACKAGE / name
        if not path.exists():
            problems.append(f"{name} is missing")
        elif path.read_text(encoding="utf-8") != text:
            problems.append(f"{name} differs from what the site builder would write")

    # Every image the reports point at has to be in the package.
    for det in data["detections"]:
        key = round(det.start_seconds * 1000)
        name = data["spectrograms"].get(key)
        if name and not (PACKAGE / SPECTROGRAM_DIR / name).exists():
            problems.append(f"missing spectrogram {name}")
    for photo in data["photos"].values():
        if not (PACKAGE / PHOTO_DIR / photo.file_name).exists():
            problems.append(f"missing photograph {photo.file_name}")

    if problems:
        print("  package is out of date:")
        for problem in sorted(set(problems)):
            print(f"    - {problem}")
        print("  run: python3 tools/build_birdidpv_package.py")
        return 1
    print(
        f"  package matches its inputs "
        f"({len(data['detections'])} detections, {len(data['photos'])} photographs, "
        f"{len(data['spectrograms'])} spectrograms)"
    )
    return 0


STAGES = ("analyse", "references", "render", "site", "check", "all")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_birdidpv_package.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "stages",
        nargs="*",
        default=["render", "site"],
        choices=STAGES,
        help="stages to run (default: render site)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"source WAV for the analyse stage (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--xc-key",
        help="xeno-canto API key for the references stage",
    )
    parser.add_argument(
        "--birdidpv",
        type=Path,
        help="birdidpv executable with the birdnet extra (default: found on PATH)",
    )
    args = parser.parse_args(argv)

    stages = list(args.stages)
    if "all" in stages:
        stages = ["analyse", "render", "site"]

    for stage in stages:
        print(f"[{stage}]")
        if stage == "references":
            stage_references(args.xc_key)
        elif stage == "analyse":
            stage_analyse(args.source, resolve_birdidpv(args.birdidpv))
        elif stage == "render":
            stage_render()
        elif stage == "site":
            stage_site()
        elif stage == "check":
            code = stage_check()
            if code:
                return code
    return 0


if __name__ == "__main__":
    sys.exit(main())
