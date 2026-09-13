# `chucky-image-corpus` binary format

The `format` object in `manifest.json` identifies the binary format and its
version. The corpus and individual datasets have separate versions.

## Version 2

`datasets` contains the datasets in the corpus. Each dataset records its
identity, version, modality, source attribution and license, and `assets`.
Each asset records its path, pixel type (`dtype`), shape and SHA-256 checksum.
Source selections and preview rendering are recorded with the asset when
available.

Each asset is one headerless, uncompressed file. Its `shape` is `[P, Y, X]`,
where all dimensions are positive. Samples are stored in little-endian,
C-contiguous order: `x` varies fastest, followed by `y`, then `plane`.

| `dtype` | Bytes per sample (`B`) | Representation |
| --- | --- | --- |
| `uint8` | 1 | Unsigned 8-bit integer |
| `uint16` | 2 | Unsigned 16-bit integer |
| `float32` | 4 | IEEE 754 binary32 |

Byte order has no effect on `uint8`. For zero-based coordinates `(p, y, x)`,
the sample begins at byte offset:

```text
B * ((p * Y + y) * X + x)
```

The required file length is `B * P * Y * X` bytes. There are no headers,
delimiters, row or plane padding, trailers, or embedded metadata. The asset's
`sha256` is the lowercase SHA-256 digest of the complete file bytes.

Pixel values retain the source's numeric representation. PNG thumbnails use
separate display adjustments and are not benchmark inputs.

Selections expressed as `start` and `stop` coordinates are zero-based with
exclusive stops, in the order named by `axes`. Acquisition labels retain the
provider's numbering where explicitly stated. Flattening selected leading
axes into `plane` does not change the C-order sample sequence.

A selection with axes `["field", "y", "x"]` contains separate 2D fields
along `plane`; that axis is neither depth nor time. For these assets, each
entry in `provenance.files` identifies the source image of a zero-based
output `plane`. The BBBC022 sample has no model-training split assignments.

## Version 1

Version 1 describes a single dataset at the top level of the manifest, with
`assets` directly under it. Its pixel type is fixed by `format.dtype` to
`uint16`, so `B = 2`. The shape, ordering, byte offsets and checksums follow
the same rules above. Existing version 1 raw files are valid version 2 assets
when their `dtype` is recorded as `uint16`; their bytes do not change.
