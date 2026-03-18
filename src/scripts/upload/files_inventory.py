import argparse
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FileListGenerator:
    """
    A class to generate a list of files in a folder and save their metadata to a CSV file.
    """

    def __init__(self, folder_path: Union[str, Path]):
        """
        Initialize the FileListGenerator with the folder path.

        Args:
            folder_path (Union[str, Path]): The path to the folder to scan for files.
        """
        self.folder_path = Path(folder_path)
        if not self.folder_path.is_dir():
            raise FileNotFoundError(f"Folder not found at: {self.folder_path}")

    def _list_files(self) -> List[Path]:
        """
        List all files in the folder recursively.

        Returns:
            List[Path]: A list of Path objects for each file.
        """
        logging.info(f"Scanning for files in {self.folder_path}...")
        return sorted([file for file in self.folder_path.rglob('*') if file.is_file()])

    def _extract_file_metadata(self, file_list: List[Path]) -> List[Dict]:
        """
        Extract metadata for each file in the provided list.

        Args:
            file_list (List[Path]): A list of file paths.

        Returns:
            List[Dict]: A list of dictionaries containing file metadata.
        """
        data = []
        for file in file_list:
            try:
                stat_info = file.stat()
                file_info = {
                    "absolute_path": str(file.resolve()),
                    "file_name": file.name,
                    "size_bytes": stat_info.st_size,
                    "modification_date": stat_info.st_mtime,
                    "relative_path": str(file.relative_to(self.folder_path)),
                }
                data.append(file_info)
            except FileNotFoundError:
                logging.warning(f"File not found during metadata extraction, skipping: {file}")
            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
        return data

    def generate_file_list(self) -> List[Dict]:
        """
        Generate a list of dictionaries containing metadata for all files in the folder.

        Returns:
            List[Dict]: A list of dictionaries with file metadata.
        """
        file_list = self._list_files()
        return self._extract_file_metadata(file_list)

    def save_to_csv(self, output_csv: Union[str, Path]) -> None:
        """
        Save the file metadata to a CSV file.

        Args:
            output_csv (Union[str, Path]): The name of the output CSV file.
        """
        file_metadata = self.generate_file_list()
        if not file_metadata:
            logging.warning("No files found to generate list.")
            return

        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        headers = file_metadata[0].keys()

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(file_metadata)
            logging.info(f"The file list has been saved to {output_path}")
        except IOError as e:
            logging.error(f"Failed to write to CSV file {output_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an inventory of files in a folder.")
    parser.add_argument("folder_path", type=str, help="The path to the folder to inventory.")
    args = parser.parse_args()

    try:
        file_generator = FileListGenerator(args.folder_path)
        output_file = f"{args.folder_path}.csv"
        file_generator.save_to_csv(output_file)
    except FileNotFoundError as e:
        logging.error(e)
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        exit(1)
