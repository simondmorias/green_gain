"""
Admin routes for system management and artifact updates.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ..services.artifact_loader import get_artifact_loader
from ..services.cache_manager import get_cache_manager
from ..services.entity_recognizer import get_entity_recognition_service
from ..services.scheduler import get_scheduler, setup_artifact_update_schedule

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(tags=["admin"], prefix="/admin")

# Simple in-memory tracking for MVP (would be database in production)
_update_history: list = []
_current_update: Optional[dict] = None


class ArtifactUpdateRequest(BaseModel):
    """Request model for manual artifact updates."""

    force_refresh: bool = False
    backup_current: bool = True


class ArtifactUpdateResponse(BaseModel):
    """Response model for artifact update operations."""

    status: str
    message: str
    update_id: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    entities_loaded: Optional[int] = None
    error: Optional[str] = None


class UpdateStatus(BaseModel):
    """Status model for ongoing updates."""

    update_id: str
    status: str
    started_at: str
    progress: str
    error: Optional[str] = None


class SchedulerTaskRequest(BaseModel):
    """Request model for scheduler task operations."""

    enabled: bool


def generate_update_id() -> str:
    """Generate a unique update ID."""
    return f"update_{int(time.time())}_{id(object())}"


async def perform_artifact_update(
    update_id: str, force_refresh: bool = False, backup_current: bool = True
) -> dict[str, Any]:
    """
    Perform artifact update in background.

    Args:
        update_id: Unique identifier for this update
        force_refresh: Whether to force refresh even if artifacts are recent
        backup_current: Whether to backup current artifacts before update

    Returns:
        Dictionary with update results
    """
    global _current_update

    start_time = time.time()
    update_record = {
        "update_id": update_id,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "force_refresh": force_refresh,
        "backup_current": backup_current,
        "progress": "Starting update...",
        "error": None,
    }

    _current_update = update_record

    try:
        # Step 1: Backup current artifacts if requested
        if backup_current:
            update_record["progress"] = "Backing up current artifacts..."
            await backup_current_artifacts(update_id)

        # Step 2: Get services
        update_record["progress"] = "Initializing services..."
        artifact_loader = get_artifact_loader()
        cache_manager = get_cache_manager()
        entity_service = get_entity_recognition_service()

        # Step 3: Clear cache if force refresh
        if force_refresh:
            update_record["progress"] = "Clearing cache..."
            artifact_loader.invalidate_cache()
            if hasattr(cache_manager, "clear_all"):
                cache_manager.clear_all()

        # Step 4: Reload artifacts
        update_record["progress"] = "Loading artifacts..."
        success = artifact_loader.reload()

        if not success:
            raise Exception("Failed to reload artifacts from loader")

        # Step 5: Update entity recognition service
        update_record["progress"] = "Updating entity recognition service..."
        entity_service.reload_artifacts()

        # Step 6: Validate loaded artifacts
        update_record["progress"] = "Validating artifacts..."
        gazetteer = artifact_loader.get_gazetteer()
        aliases = artifact_loader.get_aliases()

        total_entities = sum(len(entities) for entities in gazetteer.values())
        total_aliases = len(aliases)

        if total_entities == 0:
            logger.warning("No entities loaded - using defaults")

        # Step 7: Complete update
        end_time = time.time()
        duration = end_time - start_time

        update_record.update(
            {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": duration,
                "entities_loaded": total_entities,
                "aliases_loaded": total_aliases,
                "progress": "Update completed successfully",
            }
        )

        logger.info(
            f"Artifact update {update_id} completed successfully in {duration:.2f}s. "
            f"Loaded {total_entities} entities and {total_aliases} aliases."
        )

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        error_msg = str(e)

        update_record.update(
            {
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": duration,
                "error": error_msg,
                "progress": f"Update failed: {error_msg}",
            }
        )

        logger.error(
            f"Artifact update {update_id} failed after {duration:.2f}s: {error_msg}"
        )

    finally:
        # Add to history and clear current
        _update_history.append(update_record.copy())
        _current_update = None

        # Keep only last 50 updates in memory
        if len(_update_history) > 50:
            _update_history.pop(0)

    return update_record


async def backup_current_artifacts(update_id: str):
    """
    Backup current artifacts before update.

    Args:
        update_id: Update ID for backup naming
    """
    try:
        artifact_loader = get_artifact_loader()

        # Get current artifacts
        gazetteer = artifact_loader.get_gazetteer()
        aliases = artifact_loader.get_aliases()

        # Create backup directory
        backup_dir = Path("backups") / "artifacts" / update_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Save current artifacts
        with open(backup_dir / "gazetteer_backup.json", "w") as f:
            json.dump(gazetteer, f, indent=2)

        with open(backup_dir / "aliases_backup.json", "w") as f:
            json.dump(aliases, f, indent=2)

        # Save metadata
        metadata = {
            "backup_id": update_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entity_count": sum(len(entities) for entities in gazetteer.values()),
            "alias_count": len(aliases),
        }

        with open(backup_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Artifacts backed up to {backup_dir}")

    except Exception as e:
        logger.error(f"Failed to backup artifacts for update {update_id}: {e}")
        # Don't fail the update for backup issues
        pass


@router.post("/artifacts/update", response_model=ArtifactUpdateResponse)
async def trigger_artifact_update(
    request: ArtifactUpdateRequest, background_tasks: BackgroundTasks
) -> ArtifactUpdateResponse:
    """
    Manually trigger an artifact update.

    This endpoint allows administrators to manually refresh entity artifacts
    from the data sources. The update runs in the background.

    Args:
        request: Update configuration options
        background_tasks: FastAPI background tasks

    Returns:
        ArtifactUpdateResponse with update status and ID
    """
    global _current_update

    # Check if update is already running
    if _current_update is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Update already in progress: {_current_update['update_id']}",
        )

    # Generate update ID and start background task
    update_id = generate_update_id()

    background_tasks.add_task(
        perform_artifact_update,
        update_id,
        request.force_refresh,
        request.backup_current,
    )

    return ArtifactUpdateResponse(
        status="started",
        message="Artifact update started in background",
        update_id=update_id,
        started_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/artifacts/update/status", response_model=UpdateStatus)
async def get_update_status() -> UpdateStatus:
    """
    Get the status of the current artifact update.

    Returns:
        UpdateStatus with current update information

    Raises:
        HTTPException: If no update is currently running
    """
    global _current_update

    if _current_update is None:
        raise HTTPException(status_code=404, detail="No update currently running")

    return UpdateStatus(
        update_id=_current_update["update_id"],
        status=_current_update["status"],
        started_at=_current_update["started_at"],
        progress=_current_update["progress"],
        error=_current_update.get("error"),
    )


@router.get("/artifacts/update/history")
async def get_update_history(limit: int = 10) -> dict[str, Any]:
    """
    Get history of artifact updates.

    Args:
        limit: Maximum number of updates to return

    Returns:
        Dictionary with update history
    """
    global _update_history

    # Return most recent updates first
    recent_updates = list(reversed(_update_history[-limit:]))

    return {
        "updates": recent_updates,
        "total_count": len(_update_history),
        "current_update": _current_update,
    }


@router.get("/scheduler/tasks")
async def get_scheduled_tasks() -> dict[str, Any]:
    """
    Get all scheduled tasks.

    Returns:
        Dictionary with scheduled task information
    """
    scheduler = get_scheduler()
    tasks = scheduler.get_all_tasks()

    return {
        "tasks": tasks,
        "scheduler_running": scheduler.running,
        "total_tasks": len(tasks),
    }


@router.post("/scheduler/tasks/{task_id}/enable")
async def enable_scheduled_task(task_id: str) -> dict[str, Any]:
    """
    Enable a scheduled task.

    Args:
        task_id: ID of the task to enable

    Returns:
        Dictionary with operation status
    """
    scheduler = get_scheduler()

    if task_id not in scheduler.tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    scheduler.enable_task(task_id)

    return {
        "status": "success",
        "message": f"Task '{task_id}' enabled",
        "task": scheduler.get_task_status(task_id),
    }


@router.post("/scheduler/tasks/{task_id}/disable")
async def disable_scheduled_task(task_id: str) -> dict[str, Any]:
    """
    Disable a scheduled task.

    Args:
        task_id: ID of the task to disable

    Returns:
        Dictionary with operation status
    """
    scheduler = get_scheduler()

    if task_id not in scheduler.tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    scheduler.disable_task(task_id)

    return {
        "status": "success",
        "message": f"Task '{task_id}' disabled",
        "task": scheduler.get_task_status(task_id),
    }


@router.post("/scheduler/setup")
async def setup_scheduler() -> dict[str, Any]:
    """
    Set up the artifact update scheduler.

    Returns:
        Dictionary with setup status
    """
    try:
        setup_artifact_update_schedule()

        scheduler = get_scheduler()
        tasks = scheduler.get_all_tasks()

        return {
            "status": "success",
            "message": "Scheduler set up successfully",
            "scheduler_running": scheduler.running,
            "tasks": tasks,
        }

    except Exception as e:
        logger.error(f"Failed to set up scheduler: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to set up scheduler: {str(e)}"
        ) from e


@router.get("/artifacts/stats")
async def get_artifact_stats() -> dict[str, Any]:
    """
    Get current artifact statistics.

    Returns:
        Dictionary with artifact statistics
    """
    try:
        artifact_loader = get_artifact_loader()
        cache_manager = get_cache_manager()
        entity_service = get_entity_recognition_service()

        # Get artifact stats
        gazetteer = artifact_loader.get_gazetteer()
        aliases = artifact_loader.get_aliases()

        entity_counts = {
            entity_type: len(entities) for entity_type, entities in gazetteer.items()
        }

        total_entities = sum(entity_counts.values())

        return {
            "artifact_stats": {
                "total_entities": total_entities,
                "entity_types": entity_counts,
                "total_aliases": len(aliases),
                "last_loaded": artifact_loader.get_stats().get("last_loaded"),
            },
            "cache_stats": cache_manager.get_stats(),
            "service_stats": entity_service.get_stats(),
            "status": "operational",
        }

    except Exception as e:
        logger.error(f"Failed to get artifact stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve artifact statistics: {str(e)}"
        ) from e


@router.post("/cache/clear")
async def clear_cache() -> dict[str, Any]:
    """
    Clear all cached data.

    Returns:
        Dictionary with cache clearing status
    """
    try:
        artifact_loader = get_artifact_loader()
        cache_manager = get_cache_manager()

        # Clear artifact cache
        artifact_success = artifact_loader.invalidate_cache()

        # Clear general cache if available
        cache_cleared = False
        if hasattr(cache_manager, "clear_all"):
            cache_manager.clear_all()
            cache_cleared = True

        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "artifact_cache_cleared": artifact_success,
            "general_cache_cleared": cache_cleared,
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}") from e


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for admin services.

    Returns:
        Dictionary with health status
    """
    try:
        artifact_loader = get_artifact_loader()
        get_cache_manager()
        get_entity_recognition_service()
        get_scheduler()

        # Check if services are working
        gazetteer = artifact_loader.get_gazetteer()
        total_entities = sum(len(entities) for entities in gazetteer.values())

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "artifact_loader": "operational",
                "cache_manager": "operational",
                "entity_service": "operational",
                "scheduler": "operational" if scheduler.running else "stopped",
            },
            "metrics": {
                "total_entities": total_entities,
                "current_update_running": _current_update is not None,
                "total_updates_performed": len(_update_history),
                "scheduled_tasks": len(scheduler.tasks),
            },
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }
