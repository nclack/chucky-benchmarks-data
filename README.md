# Microscopy benchmark data

Public microscopy samples for reproducible
[chucky][] compression benchmarks.
The corpus contains six raw files totaling 17.81 MiB, with fluorescence,
brightfield, quantitative phase and electron microscopy images.

Git stores the manifest and git-annex pointers. The raw file contents are
hosted in [GitHub releases][].

## Download

Download the files from the **Assets** section of the
[microscopy-v1 release][].
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

## Format and attribution

[manifest.json][] records each asset's shape, pixel type, SHA-256
checksum, source and license. [FORMAT.md][] describes the headerless
raw format. This release uses format version 2 and corpus version 1.

Sources: OpenCell, BBBC010, Cell Painting JUMP-Scope, DynaCell A549, and
OpenOrganelle / COSEM. Preserve the attribution and notices in
[DATA-LICENSES.md][] when redistributing. Each dataset retains
its source license.

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
