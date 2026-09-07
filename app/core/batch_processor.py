"""
PhotoPro Batch Processing Manager
Processes collections of photos asynchronously in background threads with progress callbacks.
"""
import os
import logging
import threading
from typing import List, Dict, Callable, Optional
import numpy as np

from app.core.pipeline import PhotoProPipeline, PipelineResult
from app.config.settings import AppSettings

logger = logging.getLogger(__name__)

class BatchJob:
    """Represents a single photo task in a batch queue."""
    def __init__(self, file_path: str, item_id: str):
        self.file_path = file_path
        self.item_id = item_id
        self.status = "pending"  # pending, processing, completed, error
        self.progress = 0
        self.result: Optional[PipelineResult] = None
        self.error_message: Optional[str] = None

class BatchProcessor:
    """Manages asynchronous batch processing for multi-photo jobs."""

    def __init__(self, pipeline: PhotoProPipeline):
        self.pipeline = pipeline
        self._jobs: List[BatchJob] = []
        self._is_running = False
        self._cancel_requested = False
        self._lock = threading.Lock()

        # Callbacks
        self.on_item_started: Optional[Callable[[BatchJob, int, int], None]] = None
        self.on_item_completed: Optional[Callable[[BatchJob, int, int], None]] = None
        self.on_item_failed: Optional[Callable[[BatchJob, str], None]] = None
        self.on_batch_finished: Optional[Callable[[List[BatchJob]], None]] = None

    def add_files(self, file_paths: List[str]):
        """Appends files to batch queue."""
        with self._lock:
            for fp in file_paths:
                if os.path.exists(fp):
                    item_id = f"job_{len(self._jobs) + 1}_{os.path.basename(fp)}"
                    self._jobs.append(BatchJob(fp, item_id))

    def clear(self):
        """Clears queue."""
        with self._lock:
            self._jobs.clear()

    @property
    def jobs(self) -> List[BatchJob]:
        with self._lock:
            return list(self._jobs)

    def cancel(self):
        """Requests cancellation of ongoing batch."""
        self._cancel_requested = True

    def start_batch(
        self,
        settings: Optional[AppSettings] = None,
        photo_size_key: str = "passport",
        bg_mode: str = "white",
        paper_key: str = "4R",
        copies: int = 8
    ):
        """Starts batch processing in a dedicated background worker thread."""
        if self._is_running:
            logger.warning("Batch processing already in progress.")
            return

        self._is_running = True
        self._cancel_requested = False

        worker = threading.Thread(
            target=self._run_worker,
            args=(settings, photo_size_key, bg_mode, paper_key, copies),
            daemon=True
        )
        worker.start()

    def _run_worker(
        self,
        settings: Optional[AppSettings],
        photo_size_key: str,
        bg_mode: str,
        paper_key: str,
        copies: int
    ):
        """Background thread execution loop."""
        total = len(self._jobs)
        logger.info(f"Starting batch processing of {total} photos.")

        for idx, job in enumerate(self._jobs):
            if self._cancel_requested:
                job.status = "canceled"
                break

            job.status = "processing"
            if self.on_item_started:
                self.on_item_started(job, idx + 1, total)

            try:
                img_rgb = PhotoProPipeline.load_image_rgb(job.file_path)
                result = self.pipeline.process_photo(
                    img_rgb,
                    settings=settings,
                    photo_size_key=photo_size_key,
                    bg_mode=bg_mode,
                    paper_key=paper_key,
                    copies=copies
                )
                job.result = result
                job.status = "completed"
                if self.on_item_completed:
                    self.on_item_completed(job, idx + 1, total)

            except Exception as e:
                logger.error(f"Error processing {job.file_path}: {e}")
                job.status = "error"
                job.error_message = str(e)
                if self.on_item_failed:
                    self.on_item_failed(job, str(e))

        self._is_running = False
        if self.on_batch_finished:
            self.on_batch_finished(self._jobs)
        logger.info("Batch processing finished.")
