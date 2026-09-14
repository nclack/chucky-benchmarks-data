# BBBC022 selection and import

This import produces `data/bbbc022-v1/bbbc022-mito.raw`: a uint16 array of
shape `[16, 520, 696]`, containing 11,581,440 bytes. Each plane is a separate
complete field. See the [dataset guide](../DATASETS.md#bbbc022) for a preview
and attribution.

## Acquisition and selection

The source contains U2OS Cell Painting images acquired with an ImageXpress
Micro epifluorescence microscope at 20× and 0.656 µm/pixel. This sample uses
plate 20585, MitoTracker Deep Red channel `w5`, and site 1. The uncompressed
TIFFs record 300 ms exposures, a Photometrics camera, 2×2 binning, gain 4×,
and one frame per image. Background subtraction and shading correction
are off.

Visit plate rows A–P in order. Within each row, sort the mock-control wells
and choose one using a single Python `random.Random(13)` instance. Store
site 1 from each selected well in plate-row order. Selection is independent
of image brightness or compression results.

[manifest.json](../manifest.json) records every field's source TIFF,
checksum, well, site and acquisition settings. The import preserves complete
fields without rescaling, filtering, averaging or denoising; display
adjustments apply only to the thumbnail.

## Benchmark interpretation

The sample has no model-training split assignments; N2V2 may be fitted
per field. Error relative to these noisy originals measures compression
distortion, including removed noise. It does not establish fidelity to a
known clean signal. No matched higher-SNR references or repeated exposures
were identified.

## Reproduce and verify

Use Python 3.11 or later with NumPy, tifffile and imagecodecs. The source
directory must contain `BBBC022_v1_image.csv`,
`BBBC022_v1_images_20585w5.zip`, and its extracted image directory.

Run the current importer against a separate checkout of `microscopy-v1`,
which predates this sample. Pass that checkout as `--root`:

```sh
python scripts/import_bbbc022.py plan --root /path/to/base-checkout \
  --source /path/to/bbbc022_cellpainting
python scripts/import_bbbc022.py build --root /path/to/base-checkout \
  --source /path/to/bbbc022_cellpainting
python scripts/import_bbbc022.py verify --root /path/to/base-checkout \
  --source /path/to/bbbc022_cellpainting
```

`plan` reads metadata. `build` checks source TIFFs against ZIP sizes and CRCs,
creates the raw file and thumbnail, and verifies every pixel before updating
the manifest. It refuses to overwrite existing data. `verify` checks source
and output hashes, field order and exact pixels without modifying files.

Sources: [BBBC022](https://bbbc.broadinstitute.org/BBBC022) and
[Gustafsdottir et al.](https://doi.org/10.1371/journal.pone.0080999).
See [DATA-LICENSES.md](../DATA-LICENSES.md) for the CC0 notice.
