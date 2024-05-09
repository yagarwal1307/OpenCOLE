import argparse
import json
import logging
import os
from pathlib import Path

from opencole.inference.tester import T2ITester
from opencole.schema import DetailV1

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    T2ITester.register_args(parser)

    # weights
    parser.add_argument(
        "--pretrained_model_name_or_path",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--unet_dir",
        type=str,
        help="Path to the fine-tuned UNet model for SDXL",
    )
    # I/O
    parser.add_argument("--detail_dir", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    args = parser.parse_args()
    logger.info(f"{args=}")

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        output_dir.mkdir()

    tester = T2ITester(
        **{
            k: v
            for (k, v) in vars(args).items()
            if k not in ["output_dir", "detail_dir"]
        }
    )
    json_paths = sorted(Path(args.detail_dir).glob("*.json"))
    if tester.use_chunking:
        json_paths = tester.get_chunk(json_paths)

    for i, json_path in enumerate(json_paths):
        id_ = json_path.stem
        output_path = output_dir / f"{id_}.png"
        if output_path.exists():
            logger.info(f"Skipping {output_path=} since it already exists.")
            continue

        logger.info(f"Generating {output_path=}.")
        with open(json_path, "r") as f:
            detail = DetailV1(**json.load(f))
        output = tester(detail)
        output.save(str(output_path))

        if os.environ.get("LOGLEVEL", "INFO") == "DEBUG" and i == 9:
            break


if __name__ == "__main__":
    main()
