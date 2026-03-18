import argparse
import configparser
from pathlib import Path
from typing import Dict, Optional

import boto3
import dvc.api
from botocore.exceptions import ClientError
from tqdm import tqdm
from loguru import logger


# Find DVC repository root
def find_repo_root(path: Path = Path(".")) -> Optional[Path]:
    """
    Searches for the root directory of a DVC repository by traversing
    upwards from the given path until a ".dvc" folder is found.

    Args:
        path (Path): Initial path from which to start the search.

    Returns:
        Optional[Path]: The path to the DVC repository root if found,
        otherwise None.
    """
    current_path = path.resolve()
    while current_path != current_path.parent:
        if (current_path / ".dvc").is_dir():
            return current_path
        current_path = current_path.parent
    return None


# Read DVC config (compatible with real format)
def read_dvc_config(config_path: Path, remote_name: str) -> Dict[str, str]:
    cfg = configparser.ConfigParser()
    cfg.read(config_path)

    for section in cfg.sections():
        clean = section.strip("'")
        if clean == f'remote "{remote_name}"':
            return dict(cfg[section])

    raise ValueError(f"Remote '{remote_name}' no encontrado en {config_path}")


class MinioDownloader:
    """
    Handles file downloads from an S3-compatible storage service
    (e.g., MinIO) using a DVC remote configuration.
    """

    def __init__(self, remote_config: Dict[str, str], dry_run: bool = False):
        """
        Initializes the downloader with the remote configuration.

        Args:
            remote_config (Dict[str, str]): Dictionary containing the
                required parameters to connect to the S3 service
                (endpointurl, access_key_id, secret_access_key).
            dry_run (bool): If True, no download is performed and the
                intended operation is only logged.
        """
        self.dry_run = dry_run

        self.s3 = boto3.client(
            "s3",
            endpoint_url=remote_config["endpointurl"],
            aws_access_key_id=remote_config["access_key_id"],
            aws_secret_access_key=remote_config["secret_access_key"],
        )

    @staticmethod
    def parse_s3_url(url: str) -> tuple[str, str]:
        """
        Parses an S3 URL in the format s3://bucket/key and returns
        its components.

        Args:
            url (str): S3 object URL.

        Returns:
            tuple[str, str]: A tuple containing the bucket name
            and the object key.
        """
        url = url.replace("s3://", "")
        bucket, key = url.split("/", 1)
        return bucket, key

    def download(self, s3_url: str, output_path: Path):

        bucket, key = self.parse_s3_url(s3_url)

        if self.dry_run:
            logger.info(f"[DRY-RUN] s3://{bucket}/{key} → {output_path}")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # get size for tqdm
        meta = self.s3.head_object(Bucket=bucket, Key=key)
        total = meta.get("ContentLength")

        with tqdm(total=total, unit="B", unit_scale=True, desc=output_path.name) as pbar:

            def progress(bytes_amount):
                pbar.update(bytes_amount)

            self.s3.download_file(bucket, key, str(output_path), Callback=progress)

        logger.info(f"Descargado → {output_path}")


# MAIN
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descargar archivos desde DVC + MinIO")
    parser.add_argument("ruta_dvc", help="Ruta del archivo dentro de DVC")
    parser.add_argument("--remote", default="minio")
    parser.add_argument("--output", default=".")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        repo_root = find_repo_root()
        if not repo_root:
            raise FileNotFoundError("No estás dentro de un repo DVC")

        config_path = repo_root / ".dvc/config"
        remote_config = read_dvc_config(config_path, args.remote)

        downloader = MinioDownloader(remote_config, args.dry_run)

        output_path = Path(args.output) / Path(args.ruta_dvc)

        # get real URL from DVC
        s3_url = dvc.api.get_url(
            path=args.ruta_dvc,
            repo=str(repo_root),
            remote=args.remote,
        )

        downloader.download(s3_url, output_path)

    except Exception as e:
        logger.error(f"Fallo: {e}")