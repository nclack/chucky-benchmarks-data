# Microscopy benchmark data

Small public microscopy samples for reproducible [chucky][] compression
benchmarks. The [dataset guide](DATASETS.md) provides thumbnails, descriptions,
sizes and attribution for all six datasets.

The [version 3 review corpus][review] contains seven raw files totaling
60.60 MiB. It is available for review before merge; the latest stable
release is [microscopy-v1][stable].

## Download

Download the attached `.raw` files and metadata from the [review release][review].
Browser downloads require no GitHub account. The automatically generated source
archives contain git-annex pointers rather than image pixels.

With the [GitHub CLI](https://cli.github.com/manual/gh_release_download):

```sh
gh release download microscopy-v3-rc2 \
  --repo nclack/chucky-benchmarks-data --dir microscopy-v3-rc2
cd microscopy-v3-rc2
sha256sum --check SHA256SUMS
```

Keep the seven raw files, `manifest.json`, `FORMAT.md`, `DATA-LICENSES.md`
and `SHA256SUMS` together for verification. Use the manifest from the same
release as the data. Release filenames are basenames; readers that use
manifest paths need each raw file placed at its recorded `data/...` path.
Use `microscopy-v1` in these commands to download the stable corpus.

## Optional: use git-annex

Git tracks metadata and pointers; git-annex retrieves the raw contents.
After installing Git and git-annex:

```sh
git clone --branch microscopy-v3-rc2 https://github.com/nclack/chucky-benchmarks-data.git
cd chucky-benchmarks-data
git annex init
git annex get data/
git annex fsck data/
```

This also retrieves legacy assets retained for reproducing earlier results.
To fetch one input, pass its path to `git annex get`. The message
`origin not usable by git-annex` is expected for GitHub; the built-in `web`
remote supplies the content from public release URLs.

## Format and contributions

[FORMAT.md](FORMAT.md) specifies the binary layout. [manifest.json](manifest.json)
records shapes, pixel types, selections, sources and checksums. The review
corpus uses corpus version 3 and format version 2.

Preserve the credits and notices in [DATA-LICENSES.md](DATA-LICENSES.md) when
redistributing. To add data or publish a release, follow
[CONTRIBUTING.md](CONTRIBUTING.md).

[chucky]: https://github.com/acquire-project/chucky
[review]: https://github.com/nclack/chucky-benchmarks-data/releases/tag/microscopy-v3-rc2
[stable]: https://github.com/nclack/chucky-benchmarks-data/releases/tag/microscopy-v1
