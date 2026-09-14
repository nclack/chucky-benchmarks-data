import argparse
import collections
import csv
import hashlib
import io
import json
import random
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile


DATASET_ID = "bbbc022-mito"
IMAGE_DIRECTORY = "BBBC022_v1_images_20585w5"
ARCHIVE_URL = f"https://data.broadinstitute.org/bbbc/BBBC022/{IMAGE_DIRECTORY}.zip"
METADATA_URL = "https://data.broadinstitute.org/bbbc/BBBC022/BBBC022_v1_image.csv"
IMAGE_SHAPE = (520, 696)
PLANE_BYTES = 520 * 696 * 2
FIELD_COUNT = 16
SITE = 1
SETTINGS = {
    "Exposure": "300 ms",
    "Binning": "2 x 2",
    "Gain": "Gain 2 (4x)",
    "Frames to Average": "1",
    "Subtract": "Off",
    "Shading": "Off",
}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def select_images(source):
    rows = []
    with (source / "BBBC022_v1_image.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["Image_Metadata_PlateID"] != "20585":
                if rows:
                    break
                continue
            if row["Image_Metadata_ASSAY_WELL_ROLE"] == "mock":
                rows.append(row)
    by_well = collections.defaultdict(list)
    for row in rows:
        well = row["Image_Metadata_CPD_WELL_POSITION"]
        site = int(row["Image_Metadata_Site"])
        name = row["Image_FileName_OrigMito"]
        check(Path(name).name == name, f"Unexpected source filename: {name}")
        check(name.startswith(f"IXMtest_{well}_s{site}_w5"), f"Wrong field: {name}")
        by_well[well].append(row)
    check(len(rows) == 576 and len(by_well) == 64, "Expected 64 wells and 576 fields")
    check(len({r["Image_FileName_OrigMito"] for r in rows}) == 576, "Duplicate images")
    by_plate_row = collections.defaultdict(list)
    for well, fields in by_well.items():
        sites = [int(r["Image_Metadata_Site"]) for r in fields]
        check(sorted(sites) == list(range(1, 10)), f"Wrong sites in well {well}")
        by_plate_row[well[0]].append(well)
    check(sorted(by_plate_row) == list("ABCDEFGHIJKLMNOP"), "Wrong plate rows")
    rng = random.Random(13)
    selected = []
    for plate_row in sorted(by_plate_row):
        well = rng.choice(sorted(by_plate_row[plate_row]))
        selected.append(
            next(r for r in by_well[well] if int(r["Image_Metadata_Site"]) == SITE)
        )
    return selected


def read_image(payload, name):
    with tifffile.TiffFile(io.BytesIO(payload)) as image:
        check(len(image.pages) == 1, f"Expected one TIFF page: {name}")
        page = image.pages[0]
        check(page.shape == IMAGE_SHAPE, f"Wrong image shape: {name}")
        check(
            page.dtype.kind == "u" and page.dtype.itemsize == 2, f"Wrong dtype: {name}"
        )
        check(int(page.compression) == 1, f"Expected an uncompressed TIFF: {name}")
        settings = dict(
            (key.strip(), value.strip())
            for key, separator, value in (
                line.partition(":") for line in page.description.splitlines()
            )
            if separator
        )
        for key, expected in SETTINGS.items():
            check(settings.get(key) == expected, f"Unexpected {key} in {name}")
        return page.asarray(), str(page.tags["DateTime"].value)


def area_weights(length, count):
    edges = np.linspace(0, length, count + 1)
    pixels = np.arange(length)
    weights = np.maximum(
        0,
        np.minimum(edges[1:, None], pixels + 1) - np.maximum(edges[:-1, None], pixels),
    )
    return weights / np.diff(edges)[:, None]


def write_preview(pixels, path):
    low, high = np.percentile(pixels, [1, 99.5])
    check(high > low, "Preview image has no intensity range")
    display = np.clip((pixels.astype(np.float64) - low) / (high - low), 0, 1)
    resized = area_weights(520, 96) @ display @ area_weights(696, 128).T
    canvas = np.zeros((128, 128), dtype=np.uint8)
    canvas[16:112] = np.rint(resized * 255).astype(np.uint8)
    with path.open("xb") as stream:
        stream.write(imagecodecs.png_encode(canvas))
    return {
        "plane": 0,
        "percentiles": [1, 99.5],
        "intensity_range": [float(low), float(high)],
        "resize": "area average to 128x96, centered on a black 128x128 canvas",
    }


def verify_dataset(dataset, selected, source, root):
    check(dataset["id"] == DATASET_ID, "Wrong dataset")
    check(len(dataset["assets"]) == 1, "Expected one asset")
    asset = dataset["assets"][0]
    check(asset["shape"] == [FIELD_COUNT, *IMAGE_SHAPE], "Wrong shape")
    check(asset["dtype"] == "uint16", "Wrong dtype")
    records = asset["provenance"]["files"]
    check(len(records) == len(selected) == FIELD_COUNT, "Wrong source count")
    wells = [record["well"] for record in records]
    check([well[0] for well in wells] == list("ABCDEFGHIJKLMNOP"), "Wrong well order")
    check(asset["selection"]["wells"] == wells, "Wrong well selection")
    check(asset["selection"]["sites"] == [SITE], "Wrong site selection")
    path = root / asset["path"]
    check(path.stat().st_size == FIELD_COUNT * PLANE_BYTES, f"Wrong file size: {path}")
    check(digest_file(path) == asset["sha256"], f"Wrong checksum: {path}")
    with path.open("rb") as raw:
        for plane, (record, row) in enumerate(zip(records, selected, strict=True)):
            name = row["Image_FileName_OrigMito"]
            member = f"{IMAGE_DIRECTORY}/{name}"
            check(
                record["member"] == member and record["plane"] == plane,
                "Wrong plane order",
            )
            check(
                record["well"] == row["Image_Metadata_CPD_WELL_POSITION"], "Wrong well"
            )
            check(
                record["site"] == int(row["Image_Metadata_Site"]) == SITE, "Wrong site"
            )
            check(
                record["image_number"] == int(row["ImageNumber"]), "Wrong image number"
            )
            check(record["url"] == ARCHIVE_URL, "Wrong source URL")
            payload = (source / member).read_bytes()
            check(len(payload) == record["bytes"], f"Source size changed: {name}")
            check(
                hashlib.sha256(payload).hexdigest() == record["sha256"],
                f"Source changed: {name}",
            )
            with tifffile.TiffFile(io.BytesIO(payload)) as image:
                expected = image.pages[0].asarray()
            actual = np.frombuffer(raw.read(PLANE_BYTES), dtype="<u2").reshape(
                IMAGE_SHAPE
            )
            check(np.array_equal(actual, expected), f"Pixel mismatch in plane {plane}")
        check(raw.read(1) == b"", f"Unexpected trailing bytes: {path}")
    preview = imagecodecs.png_decode((root / asset["thumbnail"]).read_bytes())
    check(
        preview.shape == (128, 128) and preview.dtype == np.uint8,
        "Wrong preview format",
    )
    print(
        f"Verified {FIELD_COUNT} complete fields, source checksums, exact pixels, and the output checksum."
    )


def build(selected, source, root):
    manifest_path = root / "manifest.json"
    original_manifest = manifest_path.read_bytes()
    manifest = json.loads(original_manifest)
    check(
        all(d["id"] != DATASET_ID for d in manifest["datasets"]),
        "Dataset already exists",
    )
    destination = root / "data/bbbc022-v1"
    check(not destination.exists(), f"Output already exists: {destination}")
    relative_path = f"data/bbbc022-v1/{DATASET_ID}.raw"
    thumbnail = f"thumbnails/{DATASET_ID}.png"
    check(not (root / thumbnail).exists(), "Preview already exists")
    source_metadata = source / "BBBC022_v1_image.csv"
    dataset = {
        "id": DATASET_ID,
        "version": 1,
        "name": "BBBC022 MitoTracker compression sample",
        "modality": "fluorescence",
        "source": {
            "collection": "Broad Bioimage Benchmark Collection: BBBC022v1",
            "url": "https://bbbc.broadinstitute.org/BBBC022",
            "attribution": "Sigrun M. Gustafsdottir and colleagues, Multiplex Cytological Profiling Assay to Measure Diverse Cellular States, PLOS ONE 8(12): e80999 (2013), https://doi.org/10.1371/journal.pone.0080999; Broad Bioimage Benchmark Collection, Ljosa and colleagues, Nature Methods (2012).",
            "license": "CC0-1.0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "accessed": datetime.now(timezone.utc).date().isoformat(),
            "changes": "Selected 16 mock-control wells from plate 20585, one per plate row A-P, site 1, MitoTracker Deep Red channel w5. Repacked complete decoded TIFF fields as headerless little-endian uint16 without rescaling, cropping, filtering, averaging, or denoising. Each output plane is a separate field, not a Z slice or timepoint.",
            "metadata": {
                "url": METADATA_URL,
                "bytes": source_metadata.stat().st_size,
                "sha256": digest_file(source_metadata),
            },
            "acquisition": {
                "modality": "widefield epifluorescence",
                "microscope": "Molecular Devices ImageXpress Micro",
                "objective_magnification": 20,
                "pixel_size_um_yx": [0.656, 0.656],
                "channel": "MitoTracker Deep Red (Cy5)",
                "excitation_emission_nm": [628, 692],
                "exposure_ms": 300,
                "camera_manufacturer": "Photometrics",
                "binning_yx": [2, 2],
                "camera_gain": "Gain 2 (4x)",
                "frames_averaged": 1,
                "background_subtraction": False,
                "shading_correction": False,
                "source_tiff_compression": "none",
                "methods_url": "https://doi.org/10.1371/journal.pone.0080999",
            },
        },
        "reference_images": "No matched higher-SNR images or repeated exposures were identified for this sample.",
        "assets": [],
    }
    with zipfile.ZipFile(source / f"{IMAGE_DIRECTORY}.zip") as archive:
        archive_members = {entry.filename: entry for entry in archive.infolist()}
    destination.mkdir(parents=True)
    (root / "thumbnails").mkdir(exist_ok=True)
    acquisition_dates = []
    hasher = hashlib.sha256()
    records = []
    with (root / relative_path).open("xb") as raw:
        for plane, row in enumerate(selected):
            name = row["Image_FileName_OrigMito"]
            member = f"{IMAGE_DIRECTORY}/{name}"
            payload = (source / member).read_bytes()
            entry = archive_members[member]
            check(len(payload) == entry.file_size, f"Wrong source size: {name}")
            check(
                zlib.crc32(payload) == entry.CRC,
                f"Source differs from ZIP entry: {name}",
            )
            pixels, acquired = read_image(payload, name)
            acquisition_dates.append(acquired)
            data = pixels.astype("<u2", copy=False).tobytes(order="C")
            raw.write(data)
            hasher.update(data)
            records.append(
                {
                    "plane": plane,
                    "well": row["Image_Metadata_CPD_WELL_POSITION"],
                    "site": int(row["Image_Metadata_Site"]),
                    "image_number": int(row["ImageNumber"]),
                    "url": ARCHIVE_URL,
                    "member": member,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
            if plane == 0:
                preview = write_preview(pixels, root / thumbnail)
    dataset["assets"].append(
        {
            "id": DATASET_ID,
            "name": "BBBC022 MitoTracker",
            "path": relative_path,
            "dtype": "uint16",
            "shape": [len(records), *IMAGE_SHAPE],
            "sha256": hasher.hexdigest(),
            "thumbnail": thumbnail,
            "selection": {
                "axes": ["field", "y", "x"],
                "plate": "20585",
                "well_role": "mock",
                "wells": [record["well"] for record in records],
                "sites": [SITE],
                "channel": "w5",
                "seed": 13,
                "method": "Visit plate rows A-P in order. For each row, sort its mock-control well IDs and choose one with a single Python random.Random(13) instance. Select site 1 and store fields in plate-row order. No selection depends on pixel values or measured compression results.",
            },
            "preview": preview,
            "provenance": {"files": records},
        }
    )
    dataset["source"]["acquisition"]["first_image_datetime"] = min(acquisition_dates)
    dataset["source"]["acquisition"]["last_image_datetime"] = max(acquisition_dates)
    print(
        f"Wrote {relative_path}: {len(records)} fields, {len(records) * PLANE_BYTES / 2**20:.2f} MiB"
    )
    verify_dataset(dataset, selected, source, root)
    check(
        manifest_path.read_bytes() == original_manifest,
        "Manifest changed during import",
    )
    manifest["datasets"].append(dataset)
    manifest["version"] += 1
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Updated manifest to corpus version {manifest['version']}.")


def main():
    parser = argparse.ArgumentParser(
        description="Import a compact BBBC022 compression sample"
    )
    parser.add_argument("command", choices=["plan", "build", "verify"])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    selected = select_images(args.source)
    if args.command == "plan":
        print(
            json.dumps(
                {
                    "wells": [
                        row["Image_Metadata_CPD_WELL_POSITION"] for row in selected
                    ],
                    "site": SITE,
                    "shape": [len(selected), *IMAGE_SHAPE],
                    "bytes": len(selected) * PLANE_BYTES,
                }
            )
        )
    elif args.command == "build":
        build(selected, args.source, args.root)
    else:
        manifest = json.loads((args.root / "manifest.json").read_text())
        dataset = next(d for d in manifest["datasets"] if d["id"] == DATASET_ID)
        verify_dataset(dataset, selected, args.source, args.root)


if __name__ == "__main__":
    main()
