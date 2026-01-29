"""Task archival logic for deleted items."""

import json
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def get_cache_dir() -> Path:
    """Get the XDG cache directory for ticktick-access."""
    # Respect XDG_CACHE_HOME, default to ~/.cache
    base = os.getenv("XDG_CACHE_HOME")
    if base:
        root = Path(base)
    else:
        root = Path.home() / ".cache"
    
    path = root / "ticktick-access"
    path.mkdir(parents=True, exist_ok=True)
    return path

def archive_deleted_task(project_id: str, task_id: str, task_data: dict, archive_path: Optional[Path] = None) -> None:
    """
    Save a snapshot of the deleted task and log the event.
    
    Args:
        project_id: The ID of the project.
        task_id: The ID of the task.
        task_data: The full task dictionary.
        archive_path: Optional directory to save the JSON snapshot. Defaults to XDG cache.
    """
    try:
        cache_dir = get_cache_dir()
        
        # 1. Determine JSON Snapshot location
        if archive_path:
            archive_dir = Path(archive_path)
        else:
            archive_dir = cache_dir / "deleted_tasks"
            
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now()
        timestamp_file = now.strftime("%Y%m%d%H%M%S")
        timestamp_log = now.strftime("%Y-%m-%d %H:%M:%S")
        
        filename = f"task_{task_id}_project_{project_id}.deleted_{timestamp_file}.json"
        json_path = archive_dir / filename
        
        with open(json_path, 'w') as f:
            json.dump(task_data, f, indent=2)
            
        # 2. Append to central Log in XDG cache
        log_path = cache_dir / "deleted-tasks.log"
        log_line = f"deleted task {task_id} in project {project_id} on {timestamp_log} | snapshot: {json_path}\n"
        
        with open(log_path, 'a') as f:
            f.write(log_line)
            
        logger.info(f"Archived deleted task {task_id} to {json_path}")
        
    except Exception as e:
        logger.error(f"Failed to archive task {task_id}: {e}")
