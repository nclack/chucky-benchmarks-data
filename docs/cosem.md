# COSEM selection and import

This import produces `data/cosem-v2/cosem-cos7-em-stack.raw`: a uint8 array
of shape `[32, 1024, 1024]`, totaling 32 MiB. See the
[dataset guide](../DATASETS.md#cosem) for a preview and attribution.

## Selection and stream use

The source selection uses zero-based coordinates and exclusive stops:

```python
s0[896:960:2, 2048:3072, 3840:4864]
```

Output plane `p` comes from source `z = 896 + 2*p`. The leading axis is
depth through one specimen; neighboring planes retain natural spatial
correlation. Selection uses fixed coordinates, independent of compression
results, and preserves the published pixels without interpolation,
averaging, filtering or rescaling.

Stream planes in order. A depth-one chunk can hold 1 MiB of source pixels;
larger chunks can span multiple planes, up to the 32 MiB sample. Record
chunk shape and any replay or padding policy. The original 512 × 512 crop
matches `output[2, 256:768, 256:768]` and remains available under
`data/cosem-v1/`.

## Acquisition and reconstruction

[FIB-SEM][fibsem] forms a depth volume by repeatedly milling the specimen
and imaging each exposed surface. This sample uses the published COS-7
`jrc_cos7-1a` reconstruction 1, `recon-1/em/fibsem-uint8/s0`.
Its [Zarr metadata][array] specifies a uint8 array of shape
`[1813, 4368, 20609]`, axes `[z, y, x]`, chunks `[64, 128, 128]`, and
lossless Zstd compression at level 6.

The [coordinate metadata][coordinates] declares a 2 nm grid; selecting
every second depth gives output spacing `[4, 2, 2]` nm. Grid spacing does
not establish physical milling pitch or imaging resolution. The current
[Figshare record][record] describes reconstruction 2 with a different,
4 nm grid.

The provider has reconstructed and aligned the volume. Earlier intensity
conversion and other preprocessing are not fully established by the array
metadata. This import preserves those published values. No matched clean
reference is included.

## Reproduce and verify

Use Python 3.11 or later with NumPy, imagecodecs, numcodecs and Zarr. Run the
current importer against a separate checkout of the earlier corpus, using
a fresh work directory:

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

`plan` reads metadata and headers for 64 source chunks, pinning their ETags
and the existing manifest. `build` downloads about 51.1 MiB, decodes 64 MiB,
and writes the raw file and thumbnail. On the cluster, run the import and
verification on an approved CPU allocation.

Before updating the manifest, the importer checks every pixel through a
separate Zarr read, verifies the overlap with the old crop, and rejects
duplicate planes. It records source object hashes and each plane's source
Z coordinate and checksum. `verify` repeats these checks without modifying
files. See [DATA-LICENSES.md](../DATA-LICENSES.md) for the CC BY 4.0 notice.

[fibsem]: https://www.janelia.org/project-team/fib-sem-technology/enhanced-fib-sem-10
[record]: https://figshare.com/articles/dataset/24898086
[array]: https://janelia-cosem-datasets.s3.amazonaws.com/jrc_cos7-1a/jrc_cos7-1a.zarr/recon-1/em/fibsem-uint8/s0/.zarray
[coordinates]: https://janelia-cosem-datasets.s3.amazonaws.com/jrc_cos7-1a/jrc_cos7-1a.zarr/recon-1/em/fibsem-uint8/.zattrs
