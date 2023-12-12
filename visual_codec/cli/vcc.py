#!/usr/bin/env python3
"""visual-codec proof of concept"""
from os import getcwd, walk, mkdir
from os import path as ospath
from json import dump, load
from struct import pack
from zipfile import ZipFile
from argparse import ArgumentParser
from dataclasses import dataclass, asdict
from ..logger import log
from ..codec import (
    bit_vector_expand,
    bit_vector_shrink,
    group_binstring,
    ungroup_binstring,
)


@dataclass(frozen=True)
class Metadata:
    """Conversion metadata class"""

    exp_factor: int
    color_bitsize: int
    original_data_bits: int
    zero_pad: int
    one_pad: int
    key_path: str
    key_size: int


def __pad_color_vector(
    vector: str, frame_width: int, frame_height: int
) -> tuple[str, int]:
    m_len = len(vector)

    frame_pixels = frame_width * frame_height

    pad = 0

    # Generate random padding unit
    u = "1" if m_len % 2 else "0"
    while m_len < frame_pixels or m_len % frame_pixels != 0:
        vector += u
        m_len += 1
        pad += 1

    return vector, pad


def __bytes_to_binary_str(buf: bytes) -> str:
    return "".join([bin(b)[2:].zfill(8) for b in buf])


def __binary_str_to_bytes(binary_str: str) -> bytes:
    byte_list = []
    for i in range(0, len(binary_str), 8):
        byte = int(binary_str[i : i + 8], 2)
        byte_list.append(byte)
    return bytes(byte_list)


def __datafile_to_zip(input_data_path: str, output_data_path: str):
    with ZipFile(output_data_path, "w") as zip_file:
        if ospath.isfile(input_data_path):
            zip_file.write(input_data_path, ospath.basename(input_data_path))
        elif ospath.isdir(input_data_path):
            for root, _, files in walk(input_data_path):
                for file in files:
                    file_path = ospath.join(root, file)
                    zip_file.write(
                        file_path, ospath.relpath(file_path, input_data_path)
                    )


def __bytes_to_zip(buf: bytes, output_data_path: str):
    with open(output_data_path, "wb") as fp:
        fp.write(buf)


def __save_key_file(key: list[int], path: str):
    with open(path, "wb") as file:
        for value in key:
            byte = pack("B", value)
            file.write(byte)


def __save_key_file(key: list[int], path: str):
    with open(path, "wb") as file:
        for value in key:
            byte = pack("B", value)
            file.write(byte)


def __load_key_file(path: str) -> list[int]:
    with open(path, "rb") as file:
        byte_data = file.read()
        key = list(byte_data)
        return key


def __save_color_vector_file(vector: str, path: str):
    with open(path, "wb") as file:
        for i in range(0, len(vector), 8):
            byte = int(vector[i : i + 8], 2)
            file.write(byte.to_bytes(1, byteorder="little"))


def __load_color_vector_file(path: str) -> str:
    with open(path, "rb") as file:
        byte_data = file.read()
        binary_str = __bytes_to_binary_str(byte_data)
        return binary_str


def __save_metadata_file(metadata: Metadata, meta_path: str):
    with open(meta_path, "w", encoding="utf-8", errors="ignore") as fp:
        dump(asdict(metadata), fp, indent=4)


def __load_metadata_file(metadata_path: str) -> Metadata:
    with open(metadata_path, "r", encoding="utf-8", errors="ignore") as fp:
        return Metadata(**load(fp))


def __serialize(
    data_path: str, exp_factor: int, color_bitsize: int, output_dir_path: str
):
    # Compress data into zip
    base_name = ospath.splitext(ospath.basename(data_path))[0]

    log.info("Zipping data: %s", data_path)
    zip_path = ospath.join(output_dir_path, f"{base_name}.zip")
    __datafile_to_zip(data_path, zip_path)
    log.info("Data compressed into zip: %s", zip_path)

    with open(zip_path, "rb") as fp:
        data_bytes = fp.read()

    # Bytes to bit string
    bitstr = __bytes_to_binary_str(data_bytes)

    original_len = len(bitstr)

    # Expand bit string by exp_factor
    if exp_factor > 1:
        log.info("Applying bit expansion of %d", exp_factor)
        bitstr = bit_vector_expand(bitstr, exp_factor)

    # Apply color matrix conversion and save metadata
    # Also retrieve padding bits (can be either two groups of padding or one)
    log.info("Converting %d bits into a color vector...", len(bitstr))
    bitstr, zpad, opad, key = group_binstring(bitstr, color_bitsize)

    vector_path = ospath.join(output_dir_path, f"{base_name}.cvector")
    __save_color_vector_file(bitstr, vector_path)

    log.info("Color vector saved into: %s", vector_path)

    key_path = ospath.join(output_dir_path, f"{base_name}.key")
    __save_key_file(key, key_path)
    log.info("Key saved into: %s", key_path)

    meta_path = ospath.join(output_dir_path, f"{base_name}_metadata.json")
    __save_metadata_file(
        Metadata(
            exp_factor,
            color_bitsize,
            original_len,
            zpad,
            opad,
            key_path,
            len(key),
        ),
        meta_path,
    )

    log.info("Saved metadata json file into: %s", meta_path)


def __deserialize(inp_data_path: str, metadata_path: str, output_dir_path: str):
    log.info("Reading metadata file: %s", metadata_path)
    metadata: Metadata = __load_metadata_file(metadata_path)

    log.info("Reading color vector file: %s", inp_data_path)
    vector = __load_color_vector_file(inp_data_path)

    log.info("Reading metadata key file: %s", metadata.key_path)
    key = __load_key_file(metadata.key_path)

    log.info("Deserializing color vector...")
    vector = ungroup_binstring(
        vector, metadata.color_bitsize, metadata.zero_pad, metadata.one_pad, key
    )

    if metadata.exp_factor > 1:
        log.info("Shrinking expanded bits by a factor of %d", metadata.exp_factor)
        vector = bit_vector_shrink(vector, metadata.exp_factor)

    if len(vector) != metadata.original_data_bits:
        log.warning(
            "Deconverted data differs of %d bits.",
            abs(len(vector) - metadata.original_data_bits),
        )
        if "y" != input("\nDo you still want to write the data zip?").strip().lower():
            return

    zip_path = ospath.join(
        output_dir_path,
        f"{ospath.splitext(ospath.basename(metadata.key_path))[0]}_data.zip",
    )

    buf = __binary_str_to_bytes(vector)
    __bytes_to_zip(buf, zip_path)

    log.info("Saved data zip into: %s", zip_path)


def main() -> None:
    """vcc main entry point"""
    parser = ArgumentParser(description="visual-codec color vector (de)compiler")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="File path to convert")
    group.add_argument("-d", "--data-dir", help="Directory path to convert")
    group.add_argument(
        "-g", "--get-data", help="File path of the image/video to restore data from"
    )

    parser.add_argument(
        "-m", "--metadata", help="Path to metadata json file", default=None, type=str
    )
    parser.add_argument(
        "-o", "--output", default=getcwd(), help="Output directory path"
    )
    parser.add_argument(
        "-e", "--exp-factor", type=int, default=1, help="Expansion factor (default: 1)"
    )
    parser.add_argument(
        "-c",
        "--color-bitsize",
        type=int,
        default=8,
        help="""\
        How many bits each white/black pixel \
        will occupy in the output color vector (default: 8)""",
    )

    args = parser.parse_args()

    if args.exp_factor < 1:
        parser.error("exp-factor must be >= 1")
    if args.color_bitsize != 1 and args.color_bitsize % 8 != 0:
        parser.error("color-bitsize can be 1 or a multiple of 8")

    if args.file:
        inp_data_path = args.file
    elif args.data_dir:
        inp_data_path = args.data_dir
    elif args.get_data:
        inp_data_path = args.get_data
    else:
        parser.error("Unknown arguments")

    if not ospath.exists(inp_data_path):
        parser.error("input data path does not exist")

    if not ospath.exists(args.output):
        if (
            "y"
            != input(
                f"Do you want to create missing output folder (y/N)? ({args.output})\n\n>>"
            )
            .strip()
            .lower()
        ):
            parser.error("Cannot ensure output directory")
        mkdir(args.output)

    return (
        __deserialize(inp_data_path, args.metadata, args.output)
        if args.get_data
        else __serialize(
            inp_data_path, args.exp_factor, args.color_bitsize, args.output
        )
    )


if __name__ == "__main__":
    main()
