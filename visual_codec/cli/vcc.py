"""visual-codec CLI utility"""

from os import getcwd, remove, mkdir
from os import path as ospath
from struct import pack
from json import dump, load
from gzip import open as gzip_open
from dataclasses import dataclass, asdict
from argparse import ArgumentParser
from visual_codec.codec import (
    group_binstring,
    ungroup_binstring,
    bit_vector_expand,
    bit_vector_shrink,
)
from visual_codec.vidmaker import cvector_to_video, video_to_cvector
from visual_codec.logger import log


@dataclass(frozen=True)
class Metadata:
    """Conversion metadata class"""

    exp_factor: int
    color_bitsize: int
    zero_pad: int
    one_pad: int
    video_pad: int


def __bytes_to_binary_str(buf: bytes) -> str:
    return "".join([bin(b)[2:].zfill(8) for b in buf])


def __binary_str_to_bytes(binary_str: str) -> bytes:
    byte_list = []
    for i in range(0, len(binary_str), 8):
        byte = int(binary_str[i : i + 8], 2)
        byte_list.append(byte)
    return bytes(byte_list)


def __save_key_file(key: list[tuple[int, int]], path: str):

    with open(f"{path}.key.data", "wb") as file:
        for a, b in key:
            byte = pack("B", a)
            file.write(byte)
            byte = pack("B", b)
            file.write(byte)

    compressed_key_path = f"{path}.key"
    with open(f"{path}.key.data", "rb") as file:
        with gzip_open(compressed_key_path, "wb") as compressed_file:
            compressed_file.write(file.read())

    remove(f"{path}.key.data")

    return compressed_key_path


def __load_key_file(path: str) -> list[tuple[int, int]]:
    with gzip_open(path, "rb") as compressed_file:
        with open(f"{path}.key.data", "wb") as file:
            file.write(compressed_file.read())
    key = []
    with open(f"{path}.key.data", "rb") as file:
        byte_data = file.read()
        for i in range(0, len(byte_data), 2):
            a = byte_data[i]
            b = byte_data[i + 1]
            key.append((a, b))
    remove(f"{path}.key.data")
    return key


def __save_metadata_file(metadata: Metadata, meta_path: str):
    with open(meta_path, "w", encoding="utf-8", errors="ignore") as fp:
        dump(asdict(metadata), fp, indent=4)


def __load_metadata_file(metadata_path: str) -> Metadata:
    with open(metadata_path, "r", encoding="utf-8", errors="ignore") as fp:
        return Metadata(**load(fp))


def serialize(
    input_data_fpath: str,
    exp_factor: int,
    color_bitsize: int,
    frame_width: str,
    frame_height: str,
    output_path: str,
) -> None:
    """Serialize .zip file into video"""

    # TODO Replace with auto zip conversion
    if ospath.splitext(input_data_fpath)[1] != ".zip":
        log.error("Only .zip files are supported conversion!")
        return

    base_name = ospath.splitext(ospath.basename(input_data_fpath))[0]

    with open(input_data_fpath, "rb") as fp:
        data_bytes = fp.read()

    bitstr = __bytes_to_binary_str(data_bytes)

    # Expand bit string by exp_factor
    if exp_factor > 1:
        log.info("Applying bit expansion of %d", exp_factor)
        bitstr = bit_vector_expand(bitstr, exp_factor)

    bitstr, zpad, opad, key = group_binstring(bitstr, color_bitsize)

    vector_bytes = __binary_str_to_bytes(bitstr)

    key_path = ospath.join(output_path, base_name)
    key_path = __save_key_file(key, key_path)
    log.info("Key saved into: %s", key_path)

    output_video_path = ospath.join(output_path, base_name + ".mp4")
    n_pad = cvector_to_video(
        vector_bytes, output_video_path, frame_width, frame_height, fps=1
    )
    log.info("Saved video file into: %s", output_video_path)

    meta_path = ospath.join(output_path, base_name + "_metadata.json")
    __save_metadata_file(
        Metadata(
            exp_factor,
            color_bitsize,
            zpad,
            opad,
            n_pad,
        ),
        meta_path,
    )
    log.info("Saved metadata json file into: %s", meta_path)


def deserialize(
    input_video_fpath: str, key_fpath: str, metadata_fpath: str, output_path: str
) -> None:
    """Deserialize video into its original data"""
    metadata = __load_metadata_file(metadata_fpath)

    log.info("Loaded metadata file: %s", metadata_fpath)

    key = __load_key_file(key_fpath)

    log.info("Loaded key file: %s", key_fpath)

    vector = video_to_cvector(input_video_fpath, metadata.video_pad)

    log.info("Parsed cvector from video: %s", metadata.video_pad)

    bitstr = __bytes_to_binary_str(vector)

    log.info("Performing deconversion using key...")
    original = ungroup_binstring(bitstr, metadata.zero_pad, metadata.one_pad, key)

    if metadata.exp_factor > 1:
        original = bit_vector_shrink(original, metadata.exp_factor)
        log.info("Shrinked data with exp_factor = %d", metadata.exp_factor)

    data_bytes = __binary_str_to_bytes(original)

    bname = ospath.splitext(ospath.basename(input_video_fpath))[0]
    out_path = ospath.join(output_path, bname + ".zip")

    with open(out_path, "wb") as fp:
        fp.write(data_bytes)

    log.info("File saved into: %s", out_path)


def main() -> None:
    """vcc main entry point"""
    parser = ArgumentParser(description="visual-codec color vector (de)compiler")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="File path to convert")
    group.add_argument(
        "-v", "--video-file", help="File path of the image/video to restore data from"
    )

    parser.add_argument(
        "-r",
        "--resolution",
        type=str,
        default="352x240",
        help="Frame size in pixels for output video, write it as such: 352x240",
    )
    parser.add_argument(
        "-k",
        "--key",
        type=str,
        default=None,
        help=".key file path used for deserialization",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        help="Path to metadata json file used for deserialization",
        default=None,
        type=str,
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

    if not ospath.isdir(args.output):
        log.info("Creating missing output folder: %s", args.output)
        mkdir(args.output)

    if args.file:
        # Serialize file

        frame_width, frame_height = args.resolution.strip().split("x", maxsplit=1)
        frame_width, frame_height = int(frame_width), int(frame_height)

        serialize(
            args.file,
            args.exp_factor,
            args.color_bitsize,
            frame_width,
            frame_height,
            args.output,
        )
    elif args.video_file:
        # Deserialize video
        deserialize(args.video_file, args.key, args.metadata, args.output)
    else:
        parser.error("Unknown arguments")


if __name__ == "__main__":
    main()
