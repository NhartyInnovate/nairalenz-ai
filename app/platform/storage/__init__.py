import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from abc import ABC, abstractmethod
from app.core.config import settings

class BaseStorage(ABC):
    @abstractmethod
    async def save_file(self, file_bytes: bytes, relative_path: str) -> None:
        """
        Save file data to the storage backend.
        relative_path is typically structured as 'YYYY/MM/unique_filename.ext'
        """
        pass

    @abstractmethod
    def resolve_path(self, relative_path: str) -> str:
        """
        Convert a relative path metadata string to its absolute target path.
        """
        pass

class LocalStorage(BaseStorage):
    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = base_dir
        # Executor to run synchronous disk writes off the main event loop thread
        self.executor = ThreadPoolExecutor(max_workers=4)

    def resolve_path(self, relative_path: str) -> str:
        """
        Normalize separators and join with the base storage directory.
        """
        clean_rel_path = relative_path.replace("\\", "/")
        return os.path.abspath(os.path.join(self.base_dir, clean_rel_path))

    async def save_file(self, file_bytes: bytes, relative_path: str) -> None:
        """
        Asynchronously write file bytes to the local filesystem.
        """
        abs_path = self.resolve_path(relative_path)
        
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        # Run file I/O in thread pool executor
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._write_file_sync, abs_path, file_bytes)

    def _write_file_sync(self, abs_path: str, file_bytes: bytes) -> None:
        with open(abs_path, "wb") as f:
            f.write(file_bytes)
