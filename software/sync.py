from dataclasses import dataclass
from typing import Dict, Set, List, Tuple
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
    def __init__(self, name: str, version: int):
        self.name = name
        self.version = version
        self.files: Dict[str, ChunkedFile] = {}
    
    def add_file(self, path: str) -> None:
        """Add a new chunked file to the package."""
        if path not in self.files:
            self.files[path] = ChunkedFile()
    
    def write_chunk(self, path: str, block_number: int, data: bytes, version: int = 1) -> bool:
        """Write a chunk to a specific file in the package."""
        if path not in self.files:
            self.add_file(path)
        if version > self.version:
            self.version = version
        return self.files[path].write_block(block_number, data, version)
    
    def read_chunk(self, path: str, block_number: int, version: int = None) -> bytes:
        """Read a chunk from a specific file in the package."""
        if path not in self.files:
            return None
        return self.files[path].read_block(block_number, version)
    
    def get_manifest(self) -> Dict:
        """
        Generate a manifest of all files and their chunk versions.
        Returns a nested dictionary structure suitable for JSON serialization.
        """
        manifest = {
            "name": self.name,
            "version": self.version,
            "files": {}
        }
        
        for path, chunked_file in self.files.items():
            manifest["files"][path] = chunked_file.get_version_map()
            
        return manifest
    
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
    
    def save_manifest(self, path: str) -> None:
        """Save the package manifest to a JSON file."""
        with open(path, 'w') as f:
            json.dump(self.get_manifest(), f, indent=2)
    
    @classmethod
    def load_manifest(cls, path: str) -> Dict:
        """Load a package manifest from a JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
