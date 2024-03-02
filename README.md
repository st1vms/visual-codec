# visual-codec

Data-to-visuals encryption codec

## Installation

Open a terminal inside the repository folder and run:

```shell
pip install -e .
```

It will install the `vcc` (visual-codec-compiler) command line utility.

## Serialization

In order to serialize a .zip file into a video run:

```shell
vcc -f /path/to/zipfile.zip -o /output/folder/path -r "352x240"
```

## Deserialization

To deserialize an .mp4 file into data, use the generated .key and .json metadata files as such:

```shell
vcc -v /path/to/video.mp4 -k /path/to/keyfile.key -m /path/to/metadata.json -o /output/folder/path
```
