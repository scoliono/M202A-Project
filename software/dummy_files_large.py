from config import FILE_DIR
from sync import Package

# Create a package with filesystem storage
pkg = Package("large-package", 1, base_path=FILE_DIR)

# Generate a large file (1 GB)
file_path = "large_file.bin"
file_size = 1 * 1024 * 1024 * 1024  # 1 GB in bytes
chunk_size = 2048  # 2 KB chunks (same as ChunkedFile block size)

# Step 1: Create a large file filled with random data
with open(file_path, "wb") as f:
    for _ in range(file_size // chunk_size):
        f.write(b'\0' * chunk_size)  # Write zero-filled chunks

# Step 2: Read the large file and write it as chunks into the package
with open(file_path, "rb") as f:
    block_number = 0
    while chunk := f.read(chunk_size):
        pkg.write_chunk("/downloads/large_file.bin", block_number, chunk, version=1)
        block_number += 1

print(f"Large file added to package with {block_number} chunks.")
