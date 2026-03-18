"""DVC file processing worker module.

This module provides a worker function that processes files through the DVC
pipeline including cleaning, verification, adding, pushing, and inventory creation.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict

from loguru import logger

from src.scripts.api.app.worker_queue import (
    get_from_queue,
    register_worker_hash,
    start_receiving,
    update_queue,
)


__VERSION__ = "1.0.4"

# Processing flags - toggle steps on/off
CLEAN: bool = True
REPRO: bool = False
VERIFY: bool = False
ADD: bool = True
PUSH: bool = True
INVENTORY: bool = True

# DVC command definitions
CLEAN_COMMAND = "rm -rf /app/.dvc/tmp && rm -rf /app/.dvc/cache"
REPRO_COMMAND = "dvc repro "
VERIFY_COMMAND = "dvc status "
ADD_COMMAND = "dvc add "
PUSH_COMMAND = "dvc push "
AFTER_PUSH_COMMAND = "git rm -r --cached "
AFTER_PUSH_COMMAND_2 = 'git commit -m "stop tracking" '
INVENTORY_COMMAND = "python /app/src/scripts/upload/files_inventory.py "


def worker_function(path: str, metadata: Dict) -> bool:
    """Processes each item from the DVC queue.

    Executes the complete DVC pipeline: clean, verify, add, push, and inventory.

    Args:
        path: The file system path to process.
        metadata: Dictionary containing task metadata and status information.

    Returns:
        True if processing completed successfully, False otherwise.
    """
    task_id = metadata.get("id")
    if not task_id:
        logger.error("No task ID found in metadata")
        return False

    if path.endswith(os.sep):
        path = path[:-1]

    push_path = f"'{path}.dvc'"
    path_obj = Path(path)
    path = f"'{path}'"

    # step 1: validate path existence and log initial metadata
    if True:
        logger.info(f"1/9 -> Starting processing for {path} with task ID {task_id}")

        # validate if path exists (folder) or file exists before processing
        if not path_obj.exists():
            print(f"Path {path} does not exist, nothing to do")
            metadata["metadata"]["status"] = "failed"
            metadata["metadata"]["detail"] = "1/9 -> Path does not exist"
            update_queue(str(task_id), metadata)
            return False

        print("\n" * 5)
        print("*" * 30)
        print(f"New item received for push with dvc pipeline processing:")
        print(f"Task ID: {task_id}")
        print(f"Path to process: {path}")
        if path_obj.is_file():
            print("The path is a file")
        elif path_obj.is_dir():
            print("The path is a directory")
        print("*" * 30)
        print("\n")

    completed = False
    # Step 2: Update status to processing and log start time and IP address
    if CLEAN:
        try:
            logger.info(
                f"2/9 -> Cleaning DVC temporary files before processing {path}."
            )
            subprocess.run(CLEAN_COMMAND, shell=True, check=True, capture_output=True)
            logger.info("Temporary files cleaned.")

            metadata["metadata"]["detail"] = "2/9 -> Cleaned"
        except subprocess.CalledProcessError:
            print(f"Data at {path} is not tracked by DVC. Adding and pushing...")
        update_queue(str(task_id), metadata)

    # Step 3: Reproduce the DVC pipeline to ensure data is up to date before processing
    if REPRO:
        try:
            logger.info(f"3/9 -> Reproducing DVC pipeline before processing {path}.")
            subprocess.run(REPRO_COMMAND, shell=True, check=True, capture_output=True)
            logger.info("Pipeline reproduced.")

            metadata["metadata"]["detail"] = "3/9 -> Reproduced"
        except subprocess.CalledProcessError:
            print(f"Data at {path} is not tracked by DVC. Adding and pushing...")
        update_queue(str(task_id), metadata)

    if not completed:
        # Step 4: Update status to processing and log start time and IP address
        if VERIFY:
            try:
                logger.info(
                    f"4/9 -> Starting verification before adding {path} to DVC."
                )
                executor_command = f"{VERIFY_COMMAND} {path}"
                print(executor_command)
                subprocess.run(
                    executor_command, shell=True, check=True, capture_output=True
                )
                logger.info("Verification completed")

                metadata["metadata"]["detail"] = "4/9 -> Verified existence"
            except subprocess.CalledProcessError as e:
                print(f"Error during verification: {e.stderr.decode().strip()}")
                metadata["metadata"]["status"] = "failed"
                metadata["metadata"]["detail"] = "4/9 -> " + str(e)
                update_queue(str(task_id), metadata)
                return False

            update_queue(str(task_id), metadata)

        # Step 5: Add to DVC, push to remote, and optionally create inventory, with error handling and metadata updates
        if ADD:
            try:
                logger.info(f"5/9 -> Adding {path} to DVC.")
                executor_command = f"{ADD_COMMAND} {path}"
                subprocess.run(
                    executor_command, shell=True, check=True, capture_output=True
                )
                logger.info("DVC add completed")

                metadata["metadata"]["detail"] = "5/9 -> DVC add"
            except subprocess.CalledProcessError as e:
                print(f"Error during DVC add: {e.stderr.decode().strip()}")
                metadata["metadata"]["status"] = "failed"
                metadata["metadata"]["detail"] = "5/9 -> " + str(e)
                update_queue(str(task_id), metadata)
                return False
            update_queue(str(task_id), metadata)

        if PUSH:
            # Step 6: Push to DVC remote storage, with error handling and metadata updates
            try:
                logger.info(f"6/9 -> Pushing {path} to remote DVC storage.")
                executor_command = f"{PUSH_COMMAND} {push_path} -v"
                subprocess.run(
                    executor_command,
                    shell=True,
                    check=True,
                    capture_output=True,
                )
                completed = True
                logger.info("DVC push completed")

                metadata["metadata"]["detail"] = "6/9 -> DVC push"
            except subprocess.CalledProcessError as e:
                print(f"Error during DVC push: {e.stderr.decode().strip()}")
                metadata["metadata"]["status"] = "failed"
                metadata["metadata"]["detail"] = "6/9 ->" + str(e)
                update_queue(str(task_id), metadata)
                return False
            update_queue(str(task_id), metadata)

            # Step 7: After successful push, remove tracking from Git and commit, with error handling and metadata updates
            try:
                logger.info(f"7/9 -> Git removing tracking for {path}")
                executor_command = f"{AFTER_PUSH_COMMAND} {path}"
                subprocess.run(
                    executor_command,
                    shell=True,
                    check=True,
                    capture_output=True,
                )
                logger.info("Git remove completed")

                metadata["metadata"]["detail"] = "7/9 -> Git remove tracking"
            except subprocess.CalledProcessError as e:
                print(f"Error during Git remove: {e.stderr.decode().strip()}")
            update_queue(str(task_id), metadata)

            # Step 8: Commit the changes to Git, with error handling and metadata updates
            try:
                logger.info(f"8/9 -> Git committing changes for {path}")
                executor_command = f"{AFTER_PUSH_COMMAND_2} {path}"
                subprocess.run(
                    executor_command,
                    shell=True,
                    check=True,
                    capture_output=True,
                )
                logger.info("Git commit completed")

                metadata["metadata"]["detail"] = "8/9 -> Git commit"
            except subprocess.CalledProcessError as e:
                print(f"Error during Git commit: {e.stderr.decode().strip()}")
            update_queue(str(task_id), metadata)

        # Step 9: Optionally create inventory after successful push, with error handling and metadata updates
        if INVENTORY and completed:
            try:
                logger.info(f"9/9 -> Creating inventory for {path} of uploaded dataset")
                executor_command = f"{INVENTORY_COMMAND} {path}"
                print(executor_command)
                subprocess.run(
                    executor_command,
                    shell=True,
                    check=True,
                    capture_output=True,
                )
                logger.info("Inventory creation completed")

                metadata["metadata"]["detail"] = "9/9 -> Created inventory (CSV)"
            except subprocess.CalledProcessError as e:
                print(f"Error creating inventory: {e.stderr.decode().strip()}")
                metadata["metadata"]["status"] = "failed"
                metadata["metadata"]["detail"] = "9/9 -> " + str(e)
                update_queue(str(task_id), metadata)
                return False
            update_queue(str(task_id), metadata)

    logger.info(f"Process completed for {path}")
    return completed


if __name__ == "__main__":
    print("\n" * 5)
    print(f"version: {__VERSION__}")
    print("\n" * 5)

    print("Worker started and waiting for tasks...")

    register_worker_hash(f"version: {__VERSION__}")

    get_from_queue(worker_function)
    start_receiving()
