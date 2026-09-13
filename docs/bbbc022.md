# BBBC022 MitoTracker compression sample

This subset contains 16 complete MitoTracker Deep Red fields from separate
mock-control wells on BBBC022 plate 20585. Each field is a 520 × 696 uint16
image. Original pixel values are preserved; the only change is repacking
TIFF pixels into a headerless little-endian raw file.

The sample is intended for lossy compression and denoising experiments.
It has no model-training split assignments.

| File | Shape `[P, Y, X]` | Bytes | Size |
| --- | --- | ---: | ---: |
| `data/bbbc022-v1/bbbc022-mito.raw` | `[16, 520, 696]` | 11,581,440 | 11.04 MiB |

**P indexes separate fields, not depth or time.** Each complete plane can
be used independently for compression or per-image denoising. Record
whether a codec processes individual fields or groups fields in a chunk.

## Selection and provenance

Visit plate rows A-P in order. For each row, sort its mock-control well IDs
and choose one using a single Python `random.Random(13)` instance. Select
site 1 from each chosen well and store the fields in plate-row order.
Selection does not depend on image brightness, denoising results, or
measured compression performance.

The wells, in output order, are A14, B14, C12, D12, E18, F02, G04, H04,
I06, J05, K23, L08, M13, N09, O12, and P11.

The dataset entry in [manifest.json](../manifest.json) records the
selection, acquisition settings, raw checksum, and each plane's source
TIFF filename, archive URL, source checksum, well, site, and image number.

## Benchmark use

Use the original noisy pixels as codec inputs and as numerical references
for compression distortion. Keep lossy reconstructions and denoised images
as separate results. For N2V2 experiments, a model may be fitted to each
field; the corpus does not prescribe an image-level training split.

Error against the noisy original measures changes to the acquisition,
including any removed noise. It is not a direct measurement of fidelity
to the underlying clean signal. No matched higher-SNR references or
repeated exposures were identified for this sample.

## Acquisition

The images are of U2OS cells from a Cell Painting assay, acquired with an
ImageXpress Micro epifluorescence microscope at 20×, 0.656 µm/pixel.
Channel `w5` is MitoTracker Deep Red (Cy5, 628/692 nm excitation/emission).
The source TIFFs record 300 ms exposures, a Photometrics camera, 2×2
binning, gain 4×, and one frame per image. Background subtraction and
shading correction are off. The TIFFs are uncompressed.

The paper's illumination correction is part of its downstream analysis
pipeline. This import uses the original acquisition TIFFs without
normalization, filtering, cropping, averaging, or denoising. The PNG
preview uses separate display adjustments and is not a benchmark input.

Sources: [BBBC022](https://bbbc.broadinstitute.org/BBBC022) and
[Gustafsdottir et al., PLOS ONE (2013)](https://doi.org/10.1371/journal.pone.0080999).
The source data and preview are CC0; see [DATA-LICENSES.md](../DATA-LICENSES.md).

## Reproduce the import

Use Python 3.11 or later with NumPy, tifffile, and imagecodecs installed.
The source directory must contain `BBBC022_v1_image.csv`,
`BBBC022_v1_images_20585w5.zip`, and its extracted image directory.
The script uses the ZIP member sizes and CRCs to check the extracted TIFFs.

```sh
python scripts/import_bbbc022.py plan --source /path/to/bbbc022_cellpainting
python scripts/import_bbbc022.py build --source /path/to/bbbc022_cellpainting
python scripts/import_bbbc022.py verify --source /path/to/bbbc022_cellpainting
```

`plan` only reads metadata. `build` creates the raw file and preview,
verifies every output pixel against its source TIFF, and adds the dataset
to the manifest. It refuses to overwrite existing data. `verify` checks
the recorded source and output checksums, exact pixels, and field order
again without modifying files.
