import argparse
import configparser
import logging
from pathlib import Path
from typing import Dict, Optional

import boto3
import dvc.api
from botocore.exceptions import ClientError
from tqdm import tqdm # Import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_repo_root(path: Path = Path('.')) -> Optional[Path]:
    """Find the DVC repository root by searching upwards for a .dvc directory."""
    p = path.resolve()
    while p != p.parent:
        if (p / ".dvc").is_dir():
            return p
        p = p.parent
    # Check the final p in case the repo root is the filesystem root
    if (p / ".dvc").is_dir():
        return p
    return None

def read_dvc_config(
    config_path: Path, remote_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Reads a DVC config file and returns the configuration for a specific remote.
    """
    if not config_path.is_file():
        raise FileNotFoundError(f"DVC config file not found at: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)

    if remote_name:
        section_name = f'remote "{remote_name}"'
        if section_name not in config:
            raise ValueError(f"Remote '{remote_name}' not found in DVC config.")
        return dict(config[section_name])

    # If no remote is specified, find the first available remote
    for section in config.sections():
        if section.startswith('remote "'):
            logging.info(f"Using first available remote: {section}")
            return dict(config[section])

    raise ValueError("No DVC remote found in config file.")


class DVCFileDownloader:
    """
    A class to download files from an S3-compatible remote using DVC API and boto3.
    """

    def __init__(self, remote_config: Dict[str, str]):
        """
        Initialize the DVCFileDownloader.
        """
        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=remote_config["endpointurl"],
                aws_access_key_id=remote_config["access_key_id"],
                aws_secret_access_key=remote_config["secret_access_key"],
            )
        except KeyError as e:
            raise ValueError(f"Missing required key in remote configuration: {e}")

    def get_dvc_file_url(self, file_path: str, repo_path: Optional[str] = None) -> str:
        """
        Get the S3 URL of a file using DVC API.
        """
        try:
            # Pass the repo path to ensure DVC looks in the right place
            data_url = dvc.api.get_url(path=file_path, repo=repo_path)
            logging.info(f"URL obtained for the file: {data_url}")
            return data_url
        except Exception as e:
            raise RuntimeError(f"Error obtaining the file URL from DVC: {e}")

    @staticmethod
    def parse_s3_url(s3_url: str) -> tuple[str, str]:
        """
        Parse an S3 URL to extract the bucket name and file key.
        """
        if not s3_url.startswith("s3://"):
            raise ValueError(f"The URL '{s3_url}' is not a valid S3 URL.")
        parts = s3_url.replace("s3://", "").split("/", 1)
        bucket_name = parts[0]
        file_key = parts[1] if len(parts) > 1 else ""
        return bucket_name, file_key

    def download_file(self, s3_url: str, download_path: Path) -> Path:
        """
        Download a file from S3 to a local path with a progress bar.
        """
        bucket_name, file_key = self.parse_s3_url(s3_url)

        download_path.parent.mkdir(parents=True, exist_ok=True)

        logging.info(f"Downloading s3://{bucket_name}/{file_key} to {download_path}")
        try:
            # Get file size for progress bar
            response = self.s3_client.head_object(Bucket=bucket_name, Key=file_key)
            total_size = int(response.get('ContentLength', 0))

            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {download_path.name}") as pbar:
                self.s3_client.download_file(
                    bucket_name,
                    file_key,
                    str(download_path),
                    Callback=lambda bytes_transferred: pbar.update(bytes_transferred)
                )
            logging.info(f"File downloaded successfully: {download_path}")
            return download_path
        except ClientError as e:
            raise RuntimeError(f"Error downloading the file from S3: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a file from a DVC S3 remote, recreating its path."
    )
    parser.add_argument("file_path", type=str, help="Path of the file relative to the dataset root in DVC (e.g., '20240220_baches/Baches/baches/file.xml').")
    parser.add_argument(
        "--dvc-config",
        type=str,
        default=".dvc/config",
        help="Path to the DVC config file, relative to the repo root.",
    )
    parser.add_argument(
        "--remote",
        type=str,
        help="Name of the DVC remote to use.",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default=".",
        help="A prefix directory for the output path.",
    )
    args = parser.parse_args()

    try:
        repo_root = find_repo_root()
        if not repo_root:
            raise FileNotFoundError("Could not find DVC repository root (.dvc directory).")

        # The path provided by the user is relative to the 'val' directory.
        relative_path = Path(args.file_path)
        output_prefix = Path(args.output_prefix)
        output_path = output_prefix / relative_path

        # Construct the full DVC path by prepending 'val/'.
        dvc_path = Path("val") / relative_path

        # Construct the path to the DVC config file
        dvc_config_path = repo_root / args.dvc_config

        # Read DVC config
        remote_config = read_dvc_config(dvc_config_path, args.remote)

        # Initialize downloader
        downloader = DVCFileDownloader(remote_config)

        # Get URL and download
        s3_url = downloader.get_dvc_file_url(str(dvc_path), repo_path=str(repo_root))
        downloader.download_file(s3_url, output_path)

    except (FileNotFoundError, ValueError, RuntimeError, KeyError) as e:
        logging.error(e)
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        exit(1)
