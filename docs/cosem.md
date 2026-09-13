# COSEM COS-7 depth sample

The version 2 COSEM sample expands a single 512 × 512 crop to 32 distinct
1024 × 1024 planes from the same COS-7 specimen. Each uint8 plane contains
1 MiB; the complete sample contains 32 MiB. The original version 1 file
and its published releases remain available for reproducing earlier results.

| Version | File | Shape `[P, Y, X]` | Size |
| --- | --- | --- | ---: |
| 1 | `data/cosem-v1/cosem-cos7-em.raw` | `[1, 512, 512]` | 256 KiB |
| 2 | `data/cosem-v2/cosem-cos7-em-stack.raw` | `[32, 1024, 1024]` | 32 MiB |

## Acquisition and source

This is focused ion beam scanning electron microscopy (FIB-SEM). An ion
beam removes a thin layer of material, and the scanning electron microscope
images the newly exposed surface. Repeating this process produces a depth
volume. These are reconstructed depth slices, not tilt-angle projections.
See the [Janelia FIB-SEM description][fibsem] and the
[COS-7 dataset record][record].

The sample uses the published `jrc_cos7-1a` reconstruction 1 array,
`recon-1/em/fibsem-uint8/s0`. Its [Zarr metadata][array] specifies shape
`[1813, 4368, 20609]`, axes `[z, y, x]`, uint8 samples and chunks of
`[64, 128, 128]`, with lossless Zstd compression at level 6.

The [reconstruction's coordinate metadata][coordinates] declares a 2 nm
spacing on each axis. This describes the published grid; it does not
establish physical milling pitch or imaging resolution. The current
Figshare record links reconstruction 2 and gives a 4 nm grid. That spacing
is not assigned to this reconstruction 1 sample.

The provider has already reconstructed and aligned the volume. The array
metadata does not establish the earlier intensity conversion or every
preprocessing step. This sample preserves the published uint8 values and
is intended to represent reconstructed EM in compression benchmarks. It
does not supply detector-original counts or a clean-reference denoising
benchmark. No matched higher-SNR reference is included.

## Selection and stream use

The exact selection, using zero-based coordinates and exclusive stops, is:

```python
s0[896:960:2, 2048:3072, 3840:4864]
```

Output plane `p` comes from source `z = 896 + 2*p`. All 32 planes use the
same 1024 × 1024 Y/X region, which contains the original 512 × 512 crop.
That original crop occurs at output plane 2, rows 256:768 and columns
256:768. The importer checks this overlap byte for byte.

The leading axis is depth through one specimen. Neighboring planes retain
natural spatial correlation; they are not independent fields or repeated
exposures. The import verifies that all 32 planes have different checksums.
Selection uses fixed coordinates and does not depend on compression scores.
The depth stride selects existing planes without averaging or interpolation.
On the published grid, the selected samples have spacing `[4, 2, 2]` nm.

Stream the planes in their recorded order. A depth-one chunk can contain up
to 1 MiB of genuine source pixels; larger chunks can span multiple planes,
up to the 32 MiB sample. Record chunk shape and any replay or padding policy
with benchmark results. Having more source planes does not automatically
change a runner configured for depth-one chunks.

## Reproduce and verify

Use Python 3.11 or later with NumPy, imagecodecs, numcodecs and Zarr installed.
Run this importer from the contribution checkout, targeting a separate
checkout of the earlier corpus. Retrieve the original crop with git-annex
and use a fresh work directory:

```sh
git clone --branch microscopy-v2-rc1 \
  https://github.com/nclack/chucky-benchmarks-data.git "$HOME/tmp/cosem-base"
git -C "$HOME/tmp/cosem-base" annex init
git -C "$HOME/tmp/cosem-base" annex get data/cosem-v1/cosem-cos7-em.raw
python scripts/import_cosem.py plan --root "$HOME/tmp/cosem-base" \
  --work "$HOME/tmp/cosem-import/source"
python scripts/import_cosem.py build --root "$HOME/tmp/cosem-base" \
  --work "$HOME/tmp/cosem-import/source"
python scripts/import_cosem.py verify --root "$HOME/tmp/cosem-base" \
  --work "$HOME/tmp/cosem-import/source"
git -C "$HOME/tmp/cosem-base" annex add data/cosem-v2/
git -C "$HOME/tmp/cosem-base" annex fsck data/cosem-v2/
```

`plan` reads two small metadata objects and headers for the 64 required
source chunks. It pins source ETags, the existing manifest and the exact
selection without downloading image chunks. `build` downloads about
51.1 MiB of compressed source chunks, decodes 64 MiB, and writes the 32 MiB
raw file plus a display thumbnail. On the cluster, run the data import and
verification on an approved CPU allocation.

The importer records source object checksums and a checksum and source Z
coordinate for every output plane. It verifies all pixels using a separate
Zarr read, verifies the overlap with the old crop, and checks for duplicate
planes before changing the manifest. Existing published raw files are
preserved. `verify` repeats the source and output checks without modifying
files. The thumbnail applies contrast adjustments only to its display copy.

The data and previews are CC BY 4.0; preserve the attribution in
[DATA-LICENSES.md](../DATA-LICENSES.md).

[fibsem]: https://www.janelia.org/project-team/fib-sem-technology/enhanced-fib-sem-10
[record]: https://figshare.com/articles/dataset/24898086
[array]: https://janelia-cosem-datasets.s3.amazonaws.com/jrc_cos7-1a/jrc_cos7-1a.zarr/recon-1/em/fibsem-uint8/s0/.zarray
[coordinates]: https://janelia-cosem-datasets.s3.amazonaws.com/jrc_cos7-1a/jrc_cos7-1a.zarr/recon-1/em/fibsem-uint8/.zattrs
