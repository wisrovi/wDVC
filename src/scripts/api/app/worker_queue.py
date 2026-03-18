"""Redis-based worker queue implementation for DVC file processing.

This module provides a robust queue system for managing file processing tasks
using Redis as the backend. It supports task submission, status tracking,
and asynchronous processing with comprehensive metadata management.
"""

import json
import os
import socket
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from wredis.hash import RedisHashManager
from wredis.queue import RedisQueueManager
from wredis.sortedset import RedisSortedSetManager

# Constants
QUEUE_NAME = "dvc:my_queue"
SORTED_SET_NAME = "dvc:my_set"
SERVER = os.getenv("REDIS_HOST", "redis")
DEFAULT_TTL = 86400  # 24 hours in seconds
IP_HOST = os.getenv("IP_HOST")

print("Connecting to Redis server at:", SERVER)


# Redis managers initialization
queue_manager = RedisQueueManager(host=SERVER, verbose=False)
hash_manager = RedisHashManager(host=SERVER, verbose=False)
sorted_set_manager = RedisSortedSetManager(host=SERVER, verbose=False)


class Status(Enum):
    """
    Represents the possible statuses of a task or item.

    Attributes:
        PENDING (int): The task is pending and has not started.
        PROCESSING (int): The task is currently being processed.
        COMPLETED (int): The task has been completed successfully.
        FAILED (int): The task failed during processing.
    """

    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3


def update_queue(_id: str, new_metadata: Dict[str, Any]) -> None:
    """
    Updates task metadata in Redis hash storage.

    Args:
        _id: The unique identifier of the task.
        new_metadata: Dictionary containing updated metadata information.
    """
    new_metadata["metadata"]["ip_address"] = IP_HOST
    hash_manager.create_hash(
        f"dvc:ticket:{_id}", "metadata", new_metadata, ttl=DEFAULT_TTL
    )


def put_in_queue(path: str) -> Dict[str, Any]:
    """Adds a file processing task to the Redis queue.

    Args:
        path: The file system path to be processed.

    Returns:
        A dictionary containing the task item with ID, path, and metadata.

    Raises:
        FileNotFoundError: If the specified path does not exist.
    """
    # Validate input path exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified path does not exist: {path}")

    queue_size = queue_manager.get_queue_length(QUEUE_NAME) + 1

    # Generate unique task identifier
    task_id = f"DVC_{str(uuid4()).replace('-', '')}"

    # Create task item with required fields
    item: Dict[str, Any] = {
        "id": task_id,
        "path": path,
        "queue_size": queue_size,
        "metadata": {
            "time_start": datetime.now().isoformat(),
            "status": "pending",
            "detail": "N/A",
            "time_processing_start": "N/A",
            "time_processing_end": "N/A",
            "ip_address": IP_HOST,
        },
    }

    # Store task metadata in Redis hash for status tracking
    hash_manager.create_hash(f"dvc:ticket:{task_id}", "metadata", item)

    # Publish task to queue for processing
    queue_manager.publish(QUEUE_NAME, item)

    sorted_set_manager.add_to_sorted_set(SORTED_SET_NAME, Status.PENDING.value, task_id)
    return item


def get_complete_set() -> Dict[str, str]:
    """Retrieves all task IDs and their statuses from the tracking set.

    Returns:
        A dictionary mapping task IDs to their current statuses.
    """
    items = sorted_set_manager.get_sorted_set(SORTED_SET_NAME, with_scores=True)
    return items


def get_Status_item(_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the status and metadata of a task by its ID.

    Args:
        _id: The unique identifier of the task.

    Returns:
        Task metadata including status and timestamps, or None if not found.
    """
    metadata = hash_manager.read_hash(f"dvc:ticket:{_id}", "metadata")
    return metadata


def get_complete_queue() -> list[Dict[str, Any]]:
    """Retrieves all items currently in the queue.

    Returns:
        List of dictionaries containing task information for all queued items.
    """
    items = queue_manager.redis_client.lrange(QUEUE_NAME, 0, -1)
    items = [json.loads(item.decode()) for item in items]
    return items


def get_from_queue(func: Callable[[str, Dict[str, Any]], Any]) -> None:
    """Creates a worker that processes tasks from the Redis queue.

    This decorator function wraps a processing function and automatically
    handles task status updates, timing, and result storage.

    Args:
        func: A function that takes a file path and metadata, returns processing results.
    """

    # global queue_manager, hash_manager

    @queue_manager.on_message(QUEUE_NAME)
    def worker(message: Dict[str, Any]) -> None:
        """Processes incoming queue messages with proper status tracking."""
        task_id = message.get("id")

        # Retrieve current metadata
        metadata = hash_manager.read_hash(f"dvc:ticket:{task_id}", "metadata")

        # Handle case where metadata might be None or invalid
        if not isinstance(metadata, dict):
            metadata = {}

        # Update status to processing
        metadata["metadata"]["time_processing_start"] = datetime.now().isoformat()
        metadata["metadata"]["status"] = "processing"
        metadata["metadata"]["ip_address"] = IP_HOST

        # Store updated metadata
        if task_id:
            update_queue(str(task_id), metadata)

        # Process the file path
        path = message.get("path")
        if path is None:
            raise ValueError("Message missing required 'path' field")

        sorted_set_manager.add_to_sorted_set(
            SORTED_SET_NAME, Status.PROCESSING.value, task_id
        )

        # Execute the provided processing function
        results = func(path, metadata)

        if results:
            sorted_set_manager.add_to_sorted_set(
                SORTED_SET_NAME, Status.COMPLETED.value, task_id
            )
        else:
            sorted_set_manager.add_to_sorted_set(
                SORTED_SET_NAME, Status.FAILED.value, task_id
            )

        # Update final status and results
        metadata["metadata"]["time_processing_end"] = datetime.now().isoformat()
        metadata["metadata"]["ip_address"] = IP_HOST
        metadata["metadata"]["status"] = "completed"
        metadata["results"] = results
        # Store final metadata
        if task_id:
            update_queue(str(task_id), metadata)


def start_receiving() -> None:
    """Starts the queue listener to begin processing incoming messages.

    This method starts the Redis queue manager and blocks while waiting
    for messages to be processed by registered workers.
    """
    queue_manager.start()
    queue_manager.wait()


def register_worker_hash(version: str) -> None:
    """
    Registers the worker's status in Redis hash for monitoring and management.
    This function creates a hash entry for the worker with its IP address, start time,
    and active status, allowing for tracking and potential cleanup of worker instances.
    """

    hash_manager.create_hash(f"worker:{IP_HOST}", "status", version, ttl=DEFAULT_TTL)
