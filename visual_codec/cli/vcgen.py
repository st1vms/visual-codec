"""visual-codec video generator"""

from os import path as ospath
from os import getcwd, mkdir
from argparse import ArgumentParser
from visual_codec.logger import log
from visual_codec.cli.vcc import Metadata

def convert_to_video(cvector_fpath: str, resolution: str, output_dir: str) -> None:
    """Converts video file back to cvector"""

    frame_width, frame_height = resolution.strip().split("x", maxsplit=1)
    frame_width, frame_height = int(frame_width), int(frame_height)

    with open(cvector_fpath, "rb") as fp:
        vector_bytes = fp.read()

    vector_len = len(vector_bytes)
    frame_size = frame_width*frame_height



    n_frames = vector_len % frame_size
    if n_frames == 0:



    print(vector_bytes)


def get_cvector(video_fpath: str, output_dir: str) -> None:
    """Extracts the ones and zeros bytes of the original color vector from the video"""


def main():
    """main entry point"""
    parser = ArgumentParser(description="visual-codec video generator/extractor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--color-vector", help="File path of .cvector")
    group.add_argument(
        "-v", "--video-file", help="Video file path to extract color vector from"
    )

    parser.add_argument(
        "-r",
        "--resolution",
        type=str,
        default="1280x720",
        help="Frame size in pixels for output video, write it as such: 1280x720",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=getcwd(),
        help="Output directory path (Defaults to current directory)",
    )

    args = parser.parse_args()
    if not ospath.isdir(args.output):
        log.info("Creating missing output directory %s", args.output)
        mkdir(args.output)

    if args.color_vector:
        if not ospath.isfile(args.color_vector):
            raise ValueError(f"Invalid file path: {args.color_vector}")
        convert_to_video(args.color_vector, args.resolution, args.output)
    elif args.video_file:
        if not ospath.isfile(args.video_file):
            raise ValueError(f"Invalid file path: {args.video_file}")
        get_cvector(args.video_file, args.output)


if __name__ == "__main__":
    main()
