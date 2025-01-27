import os
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)

def setup_project_directory(project_id: str, platform: str = 'openai', api_key: str = None) -> str:
    """
    Creates project directory structure and config file
    Returns the project directory path
    """
    try:
        base_dir = os.path.join("D:\Python\Junior Data Scientist\projects")
        project_dir = os.path.join(base_dir, project_id)
        config_dir = os.path.join(project_dir, ".databuddy")
        
        for directory in [
            project_dir,
            config_dir,
            os.path.join(project_dir, "data"),
            os.path.join(project_dir, "models"),
            os.path.join(project_dir, "reports"),
        ]:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
        config_path = os.path.join(config_dir, "config.yml")
        if not os.path.exists(config_path):
            with open(config_path, "w") as f:
                yaml.dump({
                    "platform": platform,
                    "api_key": api_key,
                    "created_at": str(Path(project_dir).stat().st_ctime)
                }, f, default_flow_style=False)
        
        return project_dir
        
    except Exception as e:
        logger.error(f"Error setting up project directory: {str(e)}")
        raise
