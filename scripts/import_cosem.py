import argparse
import copy
import hashlib
import itertools
import json
import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


DATASET_ID = "cosem-cos7-em"
SOURCE = (
    "https://janelia-cosem-datasets.s3.amazonaws.com/"
    "jrc_cos7-1a/jrc_cos7-1a.zarr/recon-1/em/fibsem-uint8"
)
SELECTION = {
    "axes": ["z", "y", "x"],
    "start": [896, 2048, 3840],
    "stop": [960, 3072, 4864],
    "step": [2, 1, 1],
}
SHAPE = [32, 1024, 1024]
RAW_PATH = "data/cosem-v2/cosem-cos7-em-stack.raw"
PREVIEW_PATH = "thumbnails/cosem-cos7-em-v2.png"
ORIGINAL_PATH = "data/cosem-v1/cosem-cos7-em.raw"
ORIGINAL_SHA256 = "bcc34b3a7e3f170c181df84e5419cd28e1995cd9b5c35801fab22bdc28c410cd"
METADATA_FILES = [
    (
        "/s0/.zarray",
        "array/.zarray",
        "e381bc76f01412343a146d640e5210ced060738ce2db4662eb1c2751cf04a60f",
    ),
    (
        "/.zattrs",
        "source-attributes.json",
        "8315b1b98222146f9391ccd9c2273d2a93ff88de24bf73cf43169e1a78f5bb7b",
    ),
]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def write_json(path, value):
    write_new(path, (json.dumps(value, indent=2) + "\n").encode())


def request(url, limit=65536, method="GET", etag=None):
    headers = {"If-Match": etag} if etag else {}
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers, method=method), timeout=30
    ) as response:
        size = int(response.headers["Content-Length"])
        check(0 < size <= limit, f"Unexpected source size: {url}")
        tag = response.headers["ETag"]
        check(tag is not None and (etag is None or tag == etag), "Source ETag changed")
        data = b"" if method == "HEAD" else response.read(limit + 1)
        if method != "HEAD":
            check(len(data) == size, f"Incomplete download: {url}")
        return data, {"url": url, "bytes": size, "etag": tag}


def prepare(root, work):
    check(not (work / "plan.json").exists(), "An import plan already exists")
    manifest_data = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_data)
    original = next(d for d in manifest["datasets"] if d["id"] == DATASET_ID)
    check(original["version"] == 1, "Prepare the import from COSEM version 1")
    check(original["assets"][0]["sha256"] == ORIGINAL_SHA256, "Wrong original crop")
    check(not (root / RAW_PATH).exists(), "The expanded sample already exists")
    records = []
    for suffix, path, expected in METADATA_FILES:
        payload, record = request(SOURCE + suffix)
        record.update(path=path, sha256=hashlib.sha256(payload).hexdigest())
        check(record["sha256"] == expected, f"Source metadata changed: {suffix}")
        write_new(work / path, payload)
        records.append(record)
    metadata = json.loads((work / "array/.zarray").read_text())
    coordinates = itertools.product(
        *[
            range(first // size, (last - 1) // size + 1)
            for first, last, size in zip(
                SELECTION["start"], SELECTION["stop"], metadata["chunks"], strict=True
            )
        ]
    )

    def describe_chunk(coordinate):
        key = "/".join(str(index) for index in coordinate)
        _, record = request(SOURCE + "/s0/" + key, limit=2**21, method="HEAD")
        record.update(path="array/" + key, coordinate=list(coordinate))
        return record

    with ThreadPoolExecutor(max_workers=2) as pool:
        chunks = list(pool.map(describe_chunk, coordinates))
    check(len(chunks) == 64, "Unexpected source chunk count")
    plan = {
        "selection": SELECTION,
        "shape": SHAPE,
        "dtype": "uint8",
        "output_bytes": math.prod(SHAPE),
        "source_chunk_bytes": sum(r["bytes"] for r in chunks),
        "source_decoded_bytes": len(chunks) * math.prod(metadata["chunks"]),
        "metadata": records,
        "chunks": chunks,
        "original_dataset": original,
        "manifest_sha256": hashlib.sha256(manifest_data).hexdigest(),
    }
    write_json(work / "plan.json", plan)
    print(
        json.dumps(
            {
                k: plan[k]
                for k in (
                    "selection",
                    "shape",
                    "dtype",
                    "output_bytes",
                    "source_chunk_bytes",
                    "source_decoded_bytes",
                )
            },
            indent=2,
        )
    )
    print(f"Prepared {work / 'plan.json'}; no image chunks downloaded.")


def read_plan(work):
    plan = json.loads((work / "plan.json").read_text())
    check(plan["selection"] == SELECTION and plan["shape"] == SHAPE, "Wrong plan")
    for record, (suffix, path, expected) in zip(
        plan["metadata"], METADATA_FILES, strict=True
    ):
        check(
            record["url"] == SOURCE + suffix and record["path"] == path,
            "Wrong metadata",
        )
        check(
            record["sha256"] == expected == digest_file(work / path), "Metadata changed"
        )
    metadata = json.loads((work / "array/.zarray").read_text())
    keys = [
        "array/" + "/".join(map(str, c))
        for c in itertools.product(range(14, 15), range(16, 24), range(30, 38))
    ]
    check([r["path"] for r in plan["chunks"]] == keys, "Wrong chunk selection")
    check(
        sum(r["bytes"] for r in plan["chunks"]) <= 64 * 2**20,
        "Source download exceeds 64 MiB",
    )
    for record in plan["chunks"]:
        check(0 < record["bytes"] <= 2**21, "Unexpected source chunk size")
        key = "/".join(map(str, record["coordinate"]))
        check(record["path"] == "array/" + key, "Wrong chunk coordinates")
        check(record["url"] == SOURCE + "/s0/" + key, "Wrong source URL")
    return plan, metadata


def download(plan, work):
    def get_chunk(record):
        path = work / record["path"]
        if path.exists():
            payload = path.read_bytes()
        else:
            payload, _ = request(
                record["url"], limit=record["bytes"], etag=record["etag"]
            )
            write_new(path, payload)
        check(len(payload) == record["bytes"], f"Cached source size changed: {path}")
        return dict(record, sha256=hashlib.sha256(payload).hexdigest())

    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(get_chunk, plan["chunks"]))
    original_files = plan["original_dataset"]["assets"][0]["provenance"]["files"]
    original_hashes = {r["url"]: r["sha256"] for r in original_files}
    for record in records:
        if record["url"] in original_hashes:
            check(
                record["sha256"] == original_hashes[record["url"]],
                "Original source changed",
            )
    write_json(work / "source-files.json", [*plan["metadata"], *records])
    print(f"Cached and hashed {len(records)} source chunks.")
    return records


def decode(plan, metadata, work):
    import imagecodecs
    import numpy as np

    pixels = np.empty(SHAPE, dtype=np.uint8)
    for record in plan["chunks"]:
        encoded = (work / record["path"]).read_bytes()
        data = imagecodecs.zstd_decode(encoded)
        check(len(data) == math.prod(metadata["chunks"]), "Wrong decoded chunk size")
        chunk = np.frombuffer(data, dtype=np.uint8).reshape(metadata["chunks"])
        z, y, x = [
            index * size - first
            for index, size, first in zip(
                record["coordinate"],
                metadata["chunks"],
                SELECTION["start"],
                strict=True,
            )
        ]
        check(z == 0, "Unexpected source depth chunk")
        pixels[:, y : y + 128, x : x + 128] = chunk[:: SELECTION["step"][0]]
    return pixels


def preview(pixels, path):
    import imagecodecs
    import numpy as np

    low, high = np.percentile(pixels, [1, 99.5])
    check(high > low, "Preview has no contrast")
    display = np.clip((pixels.astype(np.float64) - low) / (high - low), 0, 1)
    small = np.rint(display.reshape(128, 8, 128, 8).mean(axis=(1, 3)) * 255).astype(
        np.uint8
    )
    write_new(path, imagecodecs.png_encode(small))
    return {
        "plane": 2,
        "percentiles": [1, 99.5],
        "intensity_range": [float(low), float(high)],
        "resize": "area average to 128x128",
    }


def verify(dataset, work, root):
    import imagecodecs
    import numpy as np
    import zarr

    plan, _ = read_plan(work)
    check(
        dataset["version"] == 2 and len(dataset["assets"]) == 1, "Wrong dataset version"
    )
    asset = dataset["assets"][0]
    check(
        asset["path"] == RAW_PATH and asset["dtype"] == "uint8", "Wrong output format"
    )
    check(
        asset["shape"] == SHAPE and asset["selection"] == SELECTION,
        "Wrong output selection",
    )
    path = root / RAW_PATH
    check(path.stat().st_size == math.prod(SHAPE), "Wrong raw file size")
    check(digest_file(path) == asset["sha256"], "Raw file checksum mismatch")
    records = asset["provenance"]["files"]
    check(
        len(records) == len(plan["metadata"]) + len(plan["chunks"]),
        "Wrong source count",
    )
    for record, expected in zip(
        records, [*plan["metadata"], *plan["chunks"]], strict=True
    ):
        check(
            all(record[k] == v for k, v in expected.items()), "Source record mismatch"
        )
        source = work / record["path"]
        check(
            source.stat().st_size == record["bytes"], f"Source size mismatch: {source}"
        )
        check(
            digest_file(source) == record["sha256"],
            f"Source checksum mismatch: {source}",
        )
    raw = np.fromfile(path, dtype=np.uint8).reshape(SHAPE)
    selection = tuple(
        slice(a, b, c)
        for a, b, c in zip(
            SELECTION["start"], SELECTION["stop"], SELECTION["step"], strict=True
        )
    )
    with zarr.config.set({"async.concurrency": 2, "threading.max_workers": 2}):
        source_array = zarr.open_array(str(work / "array"), mode="r", zarr_format=2)
        check(
            np.array_equal(raw, source_array[selection]),
            "Source pixels differ from output",
        )
    plane_hashes = [hashlib.sha256(plane.tobytes()).hexdigest() for plane in raw]
    check(len(set(plane_hashes)) == SHAPE[0], "Duplicate output planes")
    expected_planes = [
        {"plane": p, "source_z": z, "sha256": digest}
        for p, (z, digest) in enumerate(
            zip(range(896, 960, 2), plane_hashes, strict=True)
        )
    ]
    check(asset["provenance"]["planes"] == expected_planes, "Wrong plane identities")
    original = root / ORIGINAL_PATH
    check(digest_file(original) == ORIGINAL_SHA256, "Original crop checksum changed")
    check(
        raw[2, 256:768, 256:768].tobytes() == original.read_bytes(),
        "Original crop overlap differs",
    )
    thumbnail = imagecodecs.png_decode((root / PREVIEW_PATH).read_bytes())
    check(
        thumbnail.shape == (128, 128) and thumbnail.dtype == np.uint8, "Wrong thumbnail"
    )
    changed = [float(np.mean(a != b)) for a, b in zip(raw[:-1], raw[1:], strict=True)]
    result = {
        "bytes": path.stat().st_size,
        "sha256": asset["sha256"],
        "unique_planes": len(set(plane_hashes)),
        "exact_source_pixels": True,
        "original_crop_overlap_matches": True,
        "adjacent_changed_fraction_min": min(changed),
        "adjacent_changed_fraction_max": max(changed),
    }
    print(json.dumps(result, indent=2))
    return result


def build(root, work):
    plan, metadata = read_plan(work)
    manifest_path = root / "manifest.json"
    original_manifest = manifest_path.read_bytes()
    check(
        hashlib.sha256(original_manifest).hexdigest() == plan["manifest_sha256"],
        "Manifest changed since planning",
    )
    check(
        not (root / RAW_PATH).exists() and not (root / PREVIEW_PATH).exists(),
        "Output already exists",
    )
    records = download(plan, work)
    pixels = decode(plan, metadata, work)
    write_new(root / RAW_PATH, pixels.tobytes(order="C"))
    rendering = preview(pixels[2], root / PREVIEW_PATH)
    dataset = copy.deepcopy(plan["original_dataset"])
    dataset["version"] = 2
    dataset["name"] = "OpenOrganelle COS-7 FIB-SEM depth sample"
    dataset["source"].update(
        {
            "accessed": datetime.now(timezone.utc).date().isoformat(),
            "changes": "Selected 32 depth planes at Z=896,898,...,958, Y=2048:3072 and X=3840:4864 from reconstruction 1, full-resolution s0. Repacked the published uint8 values without rescaling, interpolation, filtering, averaging, or denoising. The leading axis follows depth through one specimen.",
            "acquisition": {
                "modality": "focused ion beam scanning electron microscopy (FIB-SEM)",
                "acquisition_id": "jrc_cos7-1a",
            },
            "reconstruction": {
                "id": "recon-1",
                "url": SOURCE + "/s0",
                "axes": ["z", "y", "x"],
                "shape": metadata["shape"],
                "dtype": "uint8",
                "chunks": metadata["chunks"],
                "compressor": metadata["compressor"],
                "grid_spacing_nm": [2, 2, 2],
                "grid_metadata_url": SOURCE + "/.zattrs",
                "processing": "Provider-reconstructed and aligned uint8 volume. Earlier intensity conversion and other processing details are not established by the array metadata. Grid spacing describes this reconstruction, not a verified physical milling pitch; the current Figshare record links reconstruction 2 with a different grid.",
            },
        }
    )
    dataset["assets"] = [
        {
            "id": DATASET_ID,
            "name": "OpenOrganelle COS-7 FIB-SEM depth sample",
            "path": RAW_PATH,
            "dtype": "uint8",
            "shape": SHAPE,
            "sha256": digest_file(root / RAW_PATH),
            "thumbnail": PREVIEW_PATH,
            "selection": SELECTION,
            "preview": rendering,
            "provenance": {
                "download_bytes": sum(
                    r["bytes"] for r in [*plan["metadata"], *records]
                ),
                "files": [*plan["metadata"], *records],
                "planes": [
                    {
                        "plane": p,
                        "source_z": z,
                        "sha256": hashlib.sha256(plane.tobytes()).hexdigest(),
                    }
                    for p, (z, plane) in enumerate(
                        zip(range(896, 960, 2), pixels, strict=True)
                    )
                ],
            },
        }
    ]
    write_json(work / "dataset.json", dataset)
    result = verify(dataset, work, root)
    write_json(work / "verified.json", result)
    manifest = json.loads(original_manifest)
    index = next(i for i, d in enumerate(manifest["datasets"]) if d["id"] == DATASET_ID)
    manifest["datasets"][index] = dataset
    manifest["version"] += 1
    check(
        manifest_path.read_bytes() == original_manifest,
        "Manifest changed during import",
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Updated COSEM to version 2 and corpus to version {manifest['version']}.")


def main():
    parser = argparse.ArgumentParser(
        description="Import a COSEM depth sample for compression"
    )
    parser.add_argument("command", choices=["plan", "build", "verify"])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    if args.command == "plan":
        prepare(args.root, args.work)
    elif args.command == "build":
        build(args.root, args.work)
    else:
        manifest = json.loads((args.root / "manifest.json").read_text())
        verify(
            next(d for d in manifest["datasets"] if d["id"] == DATASET_ID),
            args.work,
            args.root,
        )


if __name__ == "__main__":
    main()
