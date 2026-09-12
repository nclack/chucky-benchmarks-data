# Data licenses

## OpenCell

The OpenCell images in `data/opencell-v1/` and their PNG previews in
`thumbnails/` are shared under
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
The [OpenCell entry in the Registry of Open Data on AWS](https://registry.opendata.aws/czb-opencell/)
identifies this license. OpenCell on AWS was accessed on 2026-09-08.

The images were produced by the OpenCell team at Chan Zuckerberg Biohub.
Credit: Nathan H. Cho and colleagues,
[OpenCell: proteome-scale endogenous tagging enables the cartography of human cellular organization](https://doi.org/10.1126/science.abi6983),
Science 375, eabi6983 (2022).

Changes in this repository:

- Raw data: selected individual Z/channel planes from the original full-field
  stacks and repacked their decoded pixels as headerless little-endian uint16
  stacks. Full Y/X planes and pixel values are preserved without rescaling.
- PNG previews: selected example planes, adjusted brightness for display, and
  reduced them to 128 × 128 pixels. The README describes the preview rendering.

When redistributing, retain creator credits, source links, license and
disclaimer notices, and descriptions of earlier changes. Identify further
changes and share adaptations under CC BY-SA 4.0 or a license permitted by its
ShareAlike terms. Do not add legal or technical restrictions that prevent uses
the license allows. The license includes a disclaimer of warranties and a
limitation of liability; see the
[full license terms](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en).

## BBBC010

The C. elegans brightfield image in `data/bbbc010-v1/` and its preview are
shared under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), as
stated on the [BBBC010 dataset page](https://bbbc.broadinstitute.org/BBBC010).
Credit: Fred Ausubel's laboratory at Massachusetts General Hospital, and the
Broad Bioimage Benchmark Collection (Ljosa and colleagues, Nature Methods,
2012). The source is the provider's version 2 image archive, accessed on
2026-09-11.

Changes: selected the brightfield image of well C05, decoded its TIFF pixels,
and repacked the complete image as little-endian uint16 without rescaling.
The preview adjusts contrast and reduces the image to fit a 128×128 canvas.

## Cell Painting JUMP-Scope

The fluorescence image in `data/jump-scope-v1/` and its preview are shared
under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), as stated
in the [Cell Painting Gallery license](https://github.com/broadinstitute/cellpainting-gallery/blob/main/LICENSE).
The image comes from `cpg0002-jump-scope`, accessed on 2026-09-11.
Credit: the JUMP Cell Painting Consortium and Broad Institute; Callum
Tromans-Coia, Nasim Jamali and colleagues,
[Assessing the performance of the Cell Painting assay across different imaging systems](https://doi.org/10.1002/cyto.a.24786),
Cytometry Part A (2023). Also credit the
[Cell Painting Gallery](https://broadinstitute.github.io/cellpainting-gallery/citing.html)
(Weisbart and colleagues, Nature Methods, 2024) and the AWS Open Data
Sponsorship Program for hosting.

Changes: selected one Yokogawa CQ1 field, timepoint, Z plane and 640 nm
channel, decoded its TIFF pixels, and repacked the complete 2000×2000 image
as little-endian uint16 without rescaling. The provider's acquisition
metadata records flat-field and geometric calibration. The preview adjusts
contrast and reduces the image to 128×128.

## DynaCell A549

The reconstructed phase image in `data/dynacell-v1/` and its preview are
shared under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), as
stated in the [DynaCell public release](https://registry.opendata.aws/dynacell/)
and its [release README](https://dynacell.s3.us-west-2.amazonaws.com/v1/README.md).
Credit: Alexandr A. Kalinin and colleagues, the DynaCell team and the
Computational Imaging Group at Biohub, led by Shalin B. Mehta.
The A549 demonstration archive was accessed on 2026-09-11.

Changes: selected one full `Phase3D` plane from the mock condition, field
`fov0006`, time index 0 and Z index 24. Decoded the archive's lossless
compression and repacked the released float32 values without rescaling.
The source is reconstructed quantitative phase, rather than camera counts.
The preview adjusts contrast and reduces the image to 128×128.

This notice covers the Biohub A549 phase data. The Allen Institute data and
predicted or segmentation channels in the wider release are not included.
When sharing, preserve attribution, source and license links, supplied
notices and descriptions of changes. See the
[full CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/legalcode.en)
for its conditions, warranty disclaimer and limitation of liability.

## OpenOrganelle / COSEM

The electron-microscopy image in `data/cosem-v1/` and its preview are shared
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), as stated in
the [COSEM public release](https://registry.opendata.aws/janelia-cosem/).
Credit: the CellMap Project Team at HHMI Janelia Research Campus, Melanie
Freeman, Harald Hess, David P. Hoffman, Andrew Moore, H. Amalia Pasolli,
Gleb Shtengel and C. Shan Xu. See the
[interphase COS-7 dataset record](https://figshare.com/articles/dataset/24898086)
for sample contributions and related publications.
The `jrc_cos7-1a` reconstruction 1 array was accessed on 2026-09-11.

Changes: selected a 512×512 region of one full-resolution plane from the
provider's reconstructed uint8 volume and repacked its decoded pixels
without rescaling. The exact coordinates are in the manifest. The preview
adjusts contrast and reduces the crop to 128×128.

When sharing, preserve attribution, source and license links, supplied
notices and descriptions of changes. See the
[full CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/legalcode.en)
for its conditions, warranty disclaimer and limitation of liability.
