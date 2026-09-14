# Contributing datasets

Git tracks the manifest, documentation, thumbnails and git-annex pointers.
Raw file contents are published as GitHub release assets. Contributors need
Git and git-annex; publishing also requires the GitHub CLI (`gh`), an
authenticated account with repository write access, Python 3.11 or later,
and `sha256sum`.

## Add or modify a dataset

1. Clone the repository, run `git annex init`, and create a working branch.
   Use `git annex get data/` if you need the existing raw files.
2. Prepare headerless raw files following [FORMAT.md](FORMAT.md). Preserve
   source pixel values, use a supported pixel type, and check that each
   file has exactly `P * Y * X * bytes_per_sample` bytes.
3. Put new data under a versioned directory such as `data/example-v1/`.
   When changing published raw data, write the replacement to a new
   directory such as `data/example-v2/`; do not edit the existing annex
   symlink's target. Use unique raw basenames within the corpus because
   GitHub release assets share one directory. Use letters, digits, dots,
   hyphens and underscores in basenames for the publishing commands below.
4. Add or update the dataset in [manifest.json](manifest.json). Record its
   stable ID, version, name, modality, source URL, attribution, license and
   transformations. For each asset, record its ID, path, `dtype`, `[P, Y, X]`
   shape and SHA-256 checksum. Include source selections and provenance
   sufficient to reproduce the sample. Add or update PNG previews under
   `thumbnails/` and record their paths and rendering settings.
5. Start new datasets at version 1. Increment an existing dataset's version
   when changing its data or metadata, and increment the top-level corpus
   version for each release that changes the corpus. Change `format.version`
   only when the format specification changes. Keep older releases intact
   so previous benchmark results remain reproducible.
6. Add a brief entry to [DATASETS.md](DATASETS.md) with thumbnails, shape,
   pixel type, size, source credit and license links. Keep detailed selection
   and import instructions under `docs/`. Record full attribution, license
   notices and changes in [DATA-LICENSES.md](DATA-LICENSES.md). Update the
   README's file count, total size, corpus version and release links.
7. Add raw files through git-annex, then stage the metadata and previews:

   ```sh
   git annex add data/example-v2/
   git add manifest.json DATASETS.md DATA-LICENSES.md README.md \
     docs/ scripts/ thumbnails/
   git diff --cached --stat
   git commit -m "data: update example dataset"
   ```

   Replace the example path with your dataset directory. Git stores the
   pointers; the raw contents still need to be uploaded during publishing.

Publish and verify a prerelease from the contribution branch before
submitting it for review. Include the release link in the PR alongside the
source, selection, and changes so reviewers can download the raw files.
Pushing the branch alone does not transfer git-annex content to GitHub.
Contributors without release permissions should arrange publication with
a maintainer. After review and merge, publish the stable release.

The [BBBC022 sample](docs/bbbc022.md) includes a reproducible import script
with source-image checksums, deterministic field selection, and exact
pixel checks. The [COSEM import](docs/cosem.md) expands an existing sample
while checking source pixels, unique planes, and overlap with its previous
version.

## Publish a prerelease for review

Run these commands in Bash from a clean checkout of the contribution commit,
after it has been pushed to the repository. The branch can be unmerged.
Each release includes every raw file referenced by its manifest, including
unchanged datasets.

Fetch any missing content with `git annex get data/`, then run
`git annex fsck data/`. Prepare a fresh staging directory under `~/tmp/`.
The script below checks raw file sizes and manifest checksums, copies the
files using their release basenames, and adds the metadata:

```sh
repo=nclack/chucky-benchmarks-data
tag=microscopy-v2-rc1
mkdir -p "$HOME/tmp"
export release_dir
release_dir=$(mktemp -d "$HOME/tmp/${tag}.XXXXXX")
python3 - <<'PY'
import hashlib
import json
import math
import os
from pathlib import Path
import shutil

manifest = json.loads(Path("manifest.json").read_text())
destination = Path(os.environ["release_dir"])
sample_bytes = {"uint8": 1, "uint16": 2, "float32": 4}
for dataset in manifest["datasets"]:
    for asset in dataset["assets"]:
        source = Path(asset["path"])
        target = destination / source.name
        shape = asset["shape"]
        if len(shape) != 3 or any(type(n) is not int or n <= 0 for n in shape):
            raise ValueError(f"Invalid shape: {source}")
        if source.stat().st_size != math.prod(shape) * sample_bytes[asset["dtype"]]:
            raise ValueError(f"Wrong file size: {source}")
        with source.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != asset["sha256"]:
            raise ValueError(f"Checksum mismatch: {source}")
        if target.exists():
            raise ValueError(f"Duplicate release basename: {source.name}")
        shutil.copyfile(source, target)
for name in ("manifest.json", "FORMAT.md", "DATA-LICENSES.md"):
    shutil.copyfile(name, destination / name)
PY
```

Use the next corpus version and a candidate suffix for `tag` (version 2,
candidate 1 is shown). Give subsequent review releases new tags and preserve
published assets. If validation fails, fix the input and repeat with a fresh
staging directory before continuing. Generate checksums with basenames
matching the downloaded assets:

```sh
(
  cd "$release_dir" &&
  sha256sum -- *.raw manifest.json FORMAT.md DATA-LICENSES.md > SHA256SUMS &&
  sha256sum --check SHA256SUMS
)
```

Write release notes to `"$HOME/tmp/${tag}-notes.md"` describing the datasets,
changes, total size, format, licenses and download instructions. State that
the release is available for contribution review. Tag the contribution
commit and create a draft containing all staged assets:

```sh
git tag -a "$tag" -m "Microscopy benchmark samples ${tag#microscopy-}"
git push origin "$tag"
gh release create "$tag" "$release_dir"/* --repo "$repo" \
  --verify-tag --draft --prerelease --latest=false \
  --title "Microscopy benchmark samples ${tag#microscopy-}" \
  --notes-file "$HOME/tmp/${tag}-notes.md"
```

Inspect the draft's notes, asset sizes, and checksums, then publish it as a
prerelease. Publishing makes the assets accessible to reviewers; a draft
requires repository write access. See the
[GitHub CLI release documentation](https://cli.github.com/manual/gh_release_create)
for these options. Publish a new version to correct released data or
metadata; preserve existing release assets and tags.

```sh
gh release edit "$tag" --repo "$repo" --draft=false --prerelease --latest=false
gh release download "$tag" --repo "$repo" --dir "$release_dir/download-check"
(cd "$release_dir/download-check" && sha256sum --check SHA256SUMS)
```

After the downloaded checksums pass, register each raw file's public URL
with git-annex. Registration records a location without verifying its
contents, so verification must happen first.

```sh
python3 - <<'PY' | while IFS= read -r path; do
import json
from pathlib import Path

for dataset in json.loads(Path("manifest.json").read_text())["datasets"]:
    for asset in dataset["assets"]:
        print(asset["path"])
PY
  key=$(git annex lookupkey "$path") || exit 1
  git annex registerurl "$key" \
    "https://github.com/$repo/releases/download/$tag/${path##*/}" || exit 1
done
git annex sync --only-annex --no-content origin
```

The final sync publishes git-annex URL records so other clones can retrieve
the release contents. See
[registerurl](https://git-annex.branchable.com/git-annex-registerurl/) and
[sync](https://git-annex.branchable.com/git-annex-sync/) for details.

Finally, use a fresh clone at the candidate tag to follow the README's
git-annex download instructions and confirm `git annex fsck data/` passes.
Update the README to link the review release, and include its download and
verification results in the contribution PR.

## Publish a stable release

After review and merge, repeat the packaging and verification steps from the
merged commit using the stable tag, such as `microscopy-v2`. Omit
`--prerelease` when creating the draft, and publish with:

```sh
gh release edit "$tag" --repo "$repo" --draft=false --prerelease=false --latest
```

Register and verify the stable download URLs as above. Update the README
to identify the new stable release. Preserve the review release and its
assets so review comments and earlier results remain reproducible.
