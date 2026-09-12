# Microscopy benchmark data

Public microscopy samples for reproducible
[chucky](https://github.com/acquire-project/chucky) compression benchmarks.
The corpus contains six raw files totaling 17.81 MiB, with fluorescence,
brightfield, quantitative phase and electron microscopy images.

Git stores the manifest and git-annex pointers. The raw file contents are
hosted in [GitHub releases](https://github.com/nclack/chucky-benchmarks-data/releases).

## Download with git-annex

Install Git and git-annex, then run:

```sh
git clone https://github.com/nclack/chucky-benchmarks-data.git
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

## Direct downloads

The [microscopy-v1 release](https://github.com/nclack/chucky-benchmarks-data/releases/tag/microscopy-v1)
contains the raw files, `manifest.json`, `FORMAT.md`, `DATA-LICENSES.md` and
`SHA256SUMS`. Download all ten assets into one directory and run:

```sh
sha256sum --check SHA256SUMS
```

Place each raw file at its path in the manifest to reconstruct the corpus
layout. Release asset names are the raw files' basenames.

## Format and attribution

[manifest.json](manifest.json) records each asset's shape, pixel type, SHA-256
checksum, source and license. [FORMAT.md](FORMAT.md) describes the headerless
raw format. This release uses format version 2 and corpus version 1.

Sources: OpenCell, BBBC010, Cell Painting JUMP-Scope, DynaCell A549, and
OpenOrganelle / COSEM. Preserve the attribution and notices in
[DATA-LICENSES.md](DATA-LICENSES.md) when redistributing. Each dataset retains
its source license.
