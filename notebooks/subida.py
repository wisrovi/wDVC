# Script to upload files to MinIO

#!/usr/bin/env python3

import argparse
import configparser
import mimetypes
import os
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig
from tqdm import tqdm
from loguru import logger


# Multipart configuration for large files
TRANSFER_CONFIG = TransferConfig(
    multipart_threshold=64 * 1024 * 1024,
    multipart_chunksize=64 * 1024 * 1024,
    max_concurrency=4,
)


def find_config():
    """
    Searches for a configuration file.

    Returns:
        Path: Path to the first configuration file found
        (.dvc/config or config.txt).

    Raises:
        FileNotFoundError: If no configuration file is found.
    """
    for p in [".dvc/config", "config.txt"]:
        if Path(p).is_file():
            return Path(p)
    raise FileNotFoundError("Neither .dvc/config nor config.txt was found")


def read_dvc_config(config_path: Path, remote_name: str) -> Dict[str, str]:
    """
    Reads the DVC configuration file and extracts the specified remote configuration.

    Args:
        config_path (Path): Path to the configuration file.
        remote_name (str): Name of the remote to retrieve.

    Returns:
        Dict[str, str]: Remote configuration parameters.

    Raises:
        ValueError: If the remote is not found in the configuration.
    """
    cfg = configparser.ConfigParser()
    cfg.read(config_path)

    for section in cfg.sections():
        clean_section = section.strip("'")  # remove surrounding single quotes

        if clean_section == f'remote "{remote_name}"':
            return dict(cfg[section])

    raise ValueError(
        f"Remote '{remote_name}' not found in {config_path}. "
        f"Available sections: {cfg.sections()}"
    )


def parse_s3_url(url: str) -> Tuple[str, str]:
    """
    Parses an S3 URL into bucket and key components.

    Args:
        url (str): S3 URL in the format s3://bucket/key

    Returns:
        Tuple[str, str]: Bucket name and object key.
    """
    url = url.replace("s3://", "")
    parts = url.split("/", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


class MinioUploader:
    """
    Handles file uploads to an S3-compatible storage service (e.g., MinIO).
    """

    def __init__(self, remote_config: Dict[str, str], dry_run=False, global_progress=False):
        """
        Initializes the uploader.

        Args:
            remote_config (Dict[str, str]): Remote configuration dictionary.
            dry_run (bool): If True, no upload is performed.
            global_progress (bool): If True, enables global progress tracking.
        """
        self.bucket, _ = parse_s3_url(remote_config["url"])
        self.dry_run = dry_run
        self.global_progress = global_progress

        endpoint = os.getenv("MINIO_ENDPOINT", remote_config["endpointurl"])
        access_key = os.getenv("MINIO_ACCESS_KEY", remote_config["access_key_id"])
        secret_key = os.getenv("MINIO_SECRET_KEY", remote_config["secret_access_key"])

        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        self.total_bytes_sent = 0
        self._lock = Lock()

    def ensure_bucket(self):
        """
        Ensures that the target bucket exists.
        Creates it if it does not exist.
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Verify bucket {self.bucket}")
            return

        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError:
            logger.info(f"Creating bucket {self.bucket}")
            self.s3.create_bucket(Bucket=self.bucket)

    def _upload_with_retries(self, local_path, object_name, extra_args):
        """
        Uploads a file with retry logic in case of failure.
        """
        for attempt in range(3):
            try:
                self.s3.upload_file(
                    str(local_path),
                    self.bucket,
                    object_name,
                    ExtraArgs=extra_args,
                    Callback=self._progress_callback,
                    Config=TRANSFER_CONFIG,
                )
                return
            except ClientError:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    def _progress_callback(self, chunk):
        """
        Tracks upload progress.
        """
        with self._lock:
            self.total_bytes_sent += chunk

        if self.global_progress:
            self.global_pbar.update(chunk)

    def upload_file(self, local_path: Path, object_name: str):
        """
        Uploads a single file to the bucket.
        """
        size = local_path.stat().st_size
        content_type, _ = mimetypes.guess_type(str(local_path))
        extra_args = {"ContentType": content_type} if content_type else {}

        if self.dry_run:
            logger.info(f"[DRY-RUN] {local_path} → s3://{self.bucket}/{object_name}")
            return

        if not self.global_progress:
            with tqdm(total=size, unit="B", unit_scale=True, desc=local_path.name, leave=False) as pbar:

                def callback(chunk):
                    pbar.update(chunk)
                    self._progress_callback(chunk)

                self.s3.upload_file(
                    str(local_path),
                    self.bucket,
                    object_name,
                    ExtraArgs=extra_args,
                    Callback=callback,
                    Config=TRANSFER_CONFIG,
                )
        else:
            self._upload_with_retries(local_path, object_name, extra_args)

        logger.info(f"Uploaded → s3://{self.bucket}/{object_name}")

    def upload_folder(self, folder: Path, prefix: Optional[str], workers: int):
        """
        Uploads all files in a folder recursively using multiple threads.
        """
        files = [f for f in folder.rglob("*") if f.is_file()]
        total_size = sum(f.stat().st_size for f in files)

        logger.info(f"{len(files)} files found")

        if self.global_progress and not self.dry_run:
            self.global_pbar = tqdm(total=total_size, unit="B", unit_scale=True, desc="TOTAL")

        def task(file_path: Path):
            rel = file_path.relative_to(folder)
            object_name = f"{prefix}/{rel}".replace("\\", "/") if prefix else str(rel).replace("\\", "/")
            self.upload_file(file_path, object_name)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(task, f) for f in files]
            for f in as_completed(futures):
                if f.exception():
                    raise f.exception()

        if self.global_progress and not self.dry_run:
            self.global_pbar.close()


def main():
    """
    Entry point of the script.
    Parses arguments and triggers upload logic.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("ruta")
    parser.add_argument("--remote", default="minio")
    parser.add_argument("--prefix")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--global-progress", action="store_true")

    args = parser.parse_args()

    start = time.time()

    try:
        config_path = find_config()
        remote_config = read_dvc_config(config_path, args.remote)

        uploader = MinioUploader(remote_config, args.dry_run, args.global_progress)
        uploader.ensure_bucket()

        path = Path(args.ruta)

        if path.is_file():
            name = path.name if not args.prefix else f"{args.prefix}/{path.name}"
            uploader.upload_file(path, name)

        elif path.is_dir():
            uploader.upload_folder(path, args.prefix, args.workers)

        duration = time.time() - start
        mb = uploader.total_bytes_sent / (1024 * 1024)

        logger.info("=" * 40)
        logger.info(f"COMPLETED {'(SIMULATION)' if args.dry_run else ''}")
        logger.info(f"Time: {duration:.2f}s")

        if not args.dry_run:
            logger.info(f"Sent: {mb:.2f} MB")
            logger.info(f"Average speed: {mb / duration:.2f} MB/s")

        logger.info("=" * 40)

    except Exception as e:
        logger.error(f"Critical failure: {e}")


if __name__ == "__main__":
    main()