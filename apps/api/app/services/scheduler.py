"""
Simple scheduler service for artifact updates.
"""

import logging
import time
from datetime import datetime, timezone
from threading import Thread
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SimpleScheduler:
    """Simple scheduler for background tasks."""

    def __init__(self):
        self.running = False
        self.tasks: dict[str, dict] = {}
        self.thread: Optional[Thread] = None

    def schedule_daily(
        self, task_id: str, hour: int, minute: int, task_func: Callable, *args, **kwargs
    ):
        """
        Schedule a task to run daily at specified time.

        Args:
            task_id: Unique identifier for the task
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            task_func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
        """
        self.tasks[task_id] = {
            "type": "daily",
            "hour": hour,
            "minute": minute,
            "func": task_func,
            "args": args,
            "kwargs": kwargs,
            "last_run": None,
            "next_run": None,
            "enabled": True,
        }

        self._calculate_next_run(task_id)
        logger.info(f"Scheduled daily task '{task_id}' at {hour:02d}:{minute:02d} UTC")

    def _calculate_next_run(self, task_id: str):
        """Calculate next run time for a task."""
        task = self.tasks[task_id]
        now = datetime.now(timezone.utc)

        # Create target time for today
        target_time = now.replace(
            hour=task["hour"], minute=task["minute"], second=0, microsecond=0
        )

        # If target time has passed today, schedule for tomorrow
        if target_time <= now:
            target_time = target_time.replace(day=target_time.day + 1)

        task["next_run"] = target_time

    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                self._check_and_run_tasks()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    def _check_and_run_tasks(self):
        """Check if any tasks need to run."""
        now = datetime.now(timezone.utc)

        for task_id, task in self.tasks.items():
            if not task["enabled"]:
                continue

            next_run = task["next_run"]
            if next_run and now >= next_run:
                try:
                    logger.info(f"Running scheduled task: {task_id}")

                    # Run the task
                    task["func"](*task["args"], **task["kwargs"])

                    # Update last run and calculate next run
                    task["last_run"] = now
                    self._calculate_next_run(task_id)

                    logger.info(
                        f"Task '{task_id}' completed. Next run: {task['next_run']}"
                    )

                except Exception as e:
                    logger.error(f"Task '{task_id}' failed: {e}")
                    # Still calculate next run even if task failed
                    self._calculate_next_run(task_id)

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get status of a specific task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task_id,
            "type": task["type"],
            "enabled": task["enabled"],
            "last_run": task["last_run"].isoformat() if task["last_run"] else None,
            "next_run": task["next_run"].isoformat() if task["next_run"] else None,
            "schedule": f"{task['hour']:02d}:{task['minute']:02d} UTC",
        }

    def get_all_tasks(self) -> dict[str, Optional[dict]]:
        """Get status of all tasks."""
        return {task_id: self.get_task_status(task_id) for task_id in self.tasks.keys()}

    def enable_task(self, task_id: str):
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id]["enabled"] = True
            self._calculate_next_run(task_id)
            logger.info(f"Task '{task_id}' enabled")

    def disable_task(self, task_id: str):
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id]["enabled"] = False
            logger.info(f"Task '{task_id}' disabled")

    def remove_task(self, task_id: str):
        """Remove a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Task '{task_id}' removed")


# Global scheduler instance
_scheduler_instance: Optional[SimpleScheduler] = None


def get_scheduler() -> SimpleScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SimpleScheduler()
    return _scheduler_instance


def setup_artifact_update_schedule():
    """Set up the daily artifact update schedule."""

    def run_artifact_update():
        """Run the artifact update task."""
        try:
            logger.info("Starting scheduled artifact update")

            # Import here to avoid circular imports
            from app.services.artifact_loader import get_artifact_loader
            from app.services.entity_recognizer import get_entity_recognition_service

            # Get services
            artifact_loader = get_artifact_loader()
            entity_service = get_entity_recognition_service()

            # Reload artifacts
            success = artifact_loader.reload()
            if success:
                entity_service.reload_artifacts()
                logger.info("Scheduled artifact update completed successfully")
            else:
                logger.error("Scheduled artifact update failed")

        except Exception as e:
            logger.error(f"Scheduled artifact update failed: {e}")

    # Schedule for 2 AM UTC daily
    scheduler = get_scheduler()
    scheduler.schedule_daily(
        task_id="artifact_update", hour=2, minute=0, task_func=run_artifact_update
    )

    # Start scheduler if not already running
    if not scheduler.running:
        scheduler.start()

    logger.info("Artifact update schedule configured for 2:00 AM UTC daily")
