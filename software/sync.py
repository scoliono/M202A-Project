from dataclasses import dataclass
import hashlib
from typing import Dict, Set, List, Optional, Tuple
from pathlib import Path
import json

class ChunkedFile:
    def __init__(self, block_size=2048):  # 2 KB default block size
        self.block_size = block_size
        self.blocks = {}  # Dictionary to store blocks with their version history
        self.total_blocks = 0
    
    def write_block(self, block_number: int, data: bytes, version: int = 1) -> bool:
        if len(data) > self.block_size:
            return False
            
        # Pad blocks that are too short
        if len(data) < self.block_size:
            data = data.ljust(self.block_size, b'\0')
            
        if block_number not in self.blocks:
            self.blocks[block_number] = {}
            self.total_blocks = max(self.total_blocks, block_number + 1)
            
        self.blocks[block_number][version] = data
        return True
    
    def read_block(self, block_number: int, version: int = None) -> bytes:
        if block_number not in self.blocks:
            return None
            
        if version is None:
            version = max(self.blocks[block_number].keys())
            
        return self.blocks[block_number].get(version)
    
    def get_block_versions(self, block_number: int) -> List[int]:
        if block_number not in self.blocks:
            return []
        return sorted(self.blocks[block_number].keys())
    
    def get_latest_version(self, block_number: int) -> int:
        versions = self.get_block_versions(block_number)
        return max(versions) if versions else None
    
    def get_version_map(self) -> Dict[int, int]:
        """
        Returns a mapping of block numbers to their latest versions.
        """
        return {block: max(versions.keys()) 
                for block, versions in self.blocks.items()}

@dataclass
class ChunkVersion:
    block_number: int
    version: int
    file_path: str

class Package:
    def __init__(self, name: str, version: int, base_path: Optional[str] = None):
        """
        Initialize a Package with optional filesystem storage.
        
        Args:
            name (str): Package name
            version (int): Package version
            base_path (str, optional): Base directory for storing package files
        """
        self.name = name
        self.version = version
        self.files: Dict[str, ChunkedFile] = {}
        
        # Setup filesystem storage
        if base_path:
            self.base_path = Path(base_path)
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.chunk_storage = self.base_path / "chunks"
            self.chunk_storage.mkdir(exist_ok=True)
            self.manifest_path = self.base_path / "manifest.json"
        else:
            self.base_path = None
            self.chunk_storage = None
            self.manifest_path = None
    
    def _generate_chunk_filename(self, file_path: str, block_number: int, version: int) -> str:
        """
        Generate a unique filename for a chunk based on its metadata.
        
        Args:
            file_path (str): Original file path
            block_number (int): Block number
            version (int): Chunk version
        
        Returns:
            str: Unique filename for the chunk
        """
        # Create a hash that includes file path, block number, and version
        hash_input = f"{file_path}:{block_number}:{version}".encode()
        file_hash = hashlib.sha256(hash_input).hexdigest()
        return f"{file_hash}.chunk"

    def load_from_filesystem(self):
        """
        Load package state from filesystem.
        Reads existing manifest and chunk files.
        """
        if not self.base_path or not self.manifest_path.exists():
            return
        
        # Load manifest
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Validate manifest package details
        if manifest['name'] != self.name or manifest['version'] != self.version:
            raise ValueError("Manifest does not match package details")
        
        # Reconstruct files from manifest
        for file_path, block_versions in manifest['files'].items():
            chunked_file = ChunkedFile()
            
            for block_number_str, version in block_versions.items():
                block_number = int(block_number_str)
                
                # Attempt to load chunk from filesystem
                chunk_filename = self._generate_chunk_filename(file_path, block_number, version)
                chunk_path = self.chunk_storage / chunk_filename
                
                if chunk_path.exists():
                    with open(chunk_path, 'rb') as f:
                        chunk_data = f.read()
                    
                    chunked_file.write_block(block_number, chunk_data, version)
            
            self.files[file_path] = chunked_file
    
    def read_chunk(self, path: str, block_number: int, version: int = None) -> bytes:
        """Read a chunk from a specific file in the package."""
        if path not in self.files:
            return None
        return self.files[path].read_block(block_number, version)
    
    def write_chunk(self, path: str, block_number: int, data: bytes, version: int = 1) -> bool:
        """
        Write a chunk to a specific file in the package, with optional filesystem storage.
        
        Args:
            path (str): File path
            block_number (int): Block number
            data (bytes): Chunk data
            version (int, optional): Chunk version
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Ensure file exists in package
        if path not in self.files:
            self.files[path] = ChunkedFile()
        
        # Write chunk to in-memory file
        success = self.files[path].write_block(block_number, data, version)
        
        # Store chunk in filesystem if base path is set
        if success and self.chunk_storage:
            chunk_filename = self._generate_chunk_filename(path, block_number, version)
            chunk_path = self.chunk_storage / chunk_filename
            
            with open(chunk_path, 'wb') as f:
                f.write(data)
            
            # Update manifest
            self.save_manifest()
        
        return success
    
    def save_manifest(self):
        """
        Save package manifest to filesystem.
        """
        if not self.base_path:
            return
        
        manifest = {
            "name": self.name,
            "version": self.version,
            "files": {}
        }
        
        for path, chunked_file in self.files.items():
            manifest["files"][path] = chunked_file.get_version_map()
        
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    @classmethod
    def load_manifest(cls, path: str) -> Dict:
        """Load a package manifest from a JSON file."""
        with open(path, 'r') as f:
            return json.load(f)

    def get_missing_chunks(self, other_manifest: Dict) -> List[ChunkVersion]:
        """
        Compare with another package manifest and return list of chunks
        that are newer in the other manifest.
        """
        missing_chunks = []
        
        for file_path, their_chunks in other_manifest["files"].items():
            our_chunks = {}
            if file_path in self.files:
                our_chunks = self.files[file_path].get_version_map()
                
            for block_number, their_version in their_chunks.items():
                block_number = int(block_number)  # Convert from JSON string if needed
                our_version = our_chunks.get(block_number, 0)
                if their_version > our_version:
                    missing_chunks.append(ChunkVersion(
                        block_number=block_number,
                        version=their_version,
                        file_path=file_path
                    ))
                    
        return missing_chunks
    
    def sync_chunks(self, other_package: 'Package', chunks_to_sync: List[ChunkVersion]) -> None:
        """
        Sync specific chunks from another package instance.
        """
        for chunk in chunks_to_sync:
            data = other_package.read_chunk(
                chunk.file_path, 
                chunk.block_number, 
                chunk.version
            )
            if data:
                self.write_chunk(
                    chunk.file_path,
                    chunk.block_number,
                    data,
                    chunk.version
                )
                if chunk.version > self.version:
                    self.version = chunk.version
    
    def sync_with_manifest(self, other_manifest: Dict, chunk_fetcher) -> None:
        """
        Sync with another package using its manifest and a chunk fetcher function.
        
        Args:
            other_manifest: Dict containing the other package's manifest
            chunk_fetcher: Callable that takes (file_path, block_number, version)
                         and returns the chunk data
        """
        missing_chunks = self.get_missing_chunks(other_manifest)
        for chunk in missing_chunks:
            data = chunk_fetcher(chunk.file_path, chunk.block_number, chunk.version)
            if data:
                self.write_chunk(
                    chunk.file_path,
                    chunk.block_number,
                    data,
                    chunk.version
                )
