# Microscopy benchmark data

Public microscopy samples for reproducible
[chucky][] compression benchmarks.
The working corpus (version 2, unreleased) contains seven raw files totaling
28.85 MiB, with fluorescence, brightfield, quantitative phase and electron
microscopy images. It includes an 11.04 MiB BBBC022 fluorescence sample
for lossy compression and denoising experiments.

Git stores the manifest and git-annex pointers. Published raw file contents
are hosted in [GitHub releases][]. The BBBC022 addition can be generated
from its original TIFFs using the
[sample import instructions](docs/bbbc022.md).

## Download

The latest published corpus is the [microscopy-v1 release][], containing
six raw files totaling 17.81 MiB. Download its files from the **Assets**
section. The BBBC022 sample is part of the unreleased version 2 corpus,
with seven raw files totaling 28.85 MiB.
Browser downloads require no GitHub account, Git or git-annex. Choose the
attached `.raw` files; the automatically generated source archives contain
pointers instead of the raw data.

To download all ten assets with the
[GitHub CLI][]:

```sh
gh release download microscopy-v1 \
  --repo nclack/chucky-benchmarks-data --dir microscopy-v1
cd microscopy-v1
sha256sum --check SHA256SUMS
```

The release includes six raw files, `manifest.json`, `FORMAT.md`,
`DATA-LICENSES.md` and `SHA256SUMS`. Keep them together for checksum
verification. Release asset names are the raw files' basenames; if your
benchmark reads paths from the manifest, move each raw file to its recorded
`data/...` path after verification. Use the manifest attached to the same
release as the data.

### Optional: download with git-annex

Install Git and git-annex, then run:

```sh
git clone --branch microscopy-v1 https://github.com/nclack/chucky-benchmarks-data.git
cd chucky-benchmarks-data
git annex init
git annex get data/
git annex fsck data/
```

The built-in `web` remote retrieves the files from their recorded release
URLs. Public downloads require no GitHub account. Pass an individual file
path to `git annex get` to download only that file.

An `origin not usable by git-annex` message during initialization is expected
for GitHub; the `web` remote supplies the content.

## Format and attribution

[manifest.json][] records each asset's shape, pixel type, SHA-256
checksum, source and license. [FORMAT.md][] describes the headerless
raw format. The published `microscopy-v1` release uses format version 2
and corpus version 1. The working corpus uses corpus version 2 and retains
format version 2.

Sources: OpenCell, BBBC010, BBBC022, Cell Painting JUMP-Scope, DynaCell A549, and
OpenOrganelle / COSEM. Preserve the attribution and notices in
[DATA-LICENSES.md][] when redistributing. Each dataset retains
its source license.

## BBBC022 compression sample

The [BBBC022 sample](docs/bbbc022.md) contains 16 complete uint16
MitoTracker fields from separate control wells on one Cell Painting plate,
with 300 ms exposures and matching camera settings. The sample has no
model-training split assignments.

The raw file has shape `[16, 520, 696]` and contains 11,581,440 bytes.
Each plane is a separate 2D field; the leading axis is a sample axis.
Pixel values are preserved without rescaling, filtering or denoising.
The manifest maps every plane to its source TIFF and checksum.

These originals provide inputs and distortion references for lossy
compression experiments. Error measured against the noisy acquisition
describes compression distortion; it does not by itself establish
fidelity to the underlying clean signal.

## Contributing

See [CONTRIBUTING.md][] for instructions on adding or modifying
a dataset and publishing a new release.

[chucky]: https://github.com/acquire-project/chucky
[GitHub releases]: https://github.com/nclack/chucky-benchmarks-data/releases
[microscopy-v1 release]: https://github.com/nclack/chucky-benchmarks-data/releases/tag/microscopy-v1
[GitHub CLI]: https://cli.github.com/manual/gh_release_download
[manifest.json]: manifest.json
[FORMAT.md]: FORMAT.md
[DATA-LICENSES.md]: DATA-LICENSES.md
[CONTRIBUTING.md]: CONTRIBUTING.md
