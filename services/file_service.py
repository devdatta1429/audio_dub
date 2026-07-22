import os
import shutil
import uuid
from pathlib import Path
from config import PROJECTS_DIR

class FileService:
    def __init__(self, project_id: str = None):
        self.project_id = project_id or str(uuid.uuid4())
        self.project_dir = PROJECTS_DIR / self.project_id
        
        # Define subdirectories
        self.dirs = {
            "input": self.project_dir / "input",
            "media": self.project_dir / "media",
            "subtitles": self.project_dir / "subtitles",
            "audio": self.project_dir / "audio",
            "transcript": self.project_dir / "transcript",
            "translation": self.project_dir / "translation",
            "tts": self.project_dir / "tts",
            "final_audio": self.project_dir / "final_audio",
            "output": self.project_dir / "output"
        }
        
    def setup_project_directories(self):
        """Creates the per-video working directory structure."""
        for name, path in self.dirs.items():
            path.mkdir(parents=True, exist_ok=True)
            
    def get_path(self, dir_name: str, file_name: str) -> Path:
        """Helper to get a path to a file in a specific project directory."""
        if dir_name not in self.dirs:
            raise ValueError(f"Directory {dir_name} not part of project structure.")
        return self.dirs[dir_name] / file_name

    def save_uploaded_file(self, uploaded_file_path: Path, original_filename: str) -> Path:
        """Copies an uploaded file into the input directory."""
        dest_path = self.get_path("input", "original_video" + uploaded_file_path.suffix)
        shutil.copy(uploaded_file_path, dest_path)
        return dest_path
