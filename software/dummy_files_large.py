from config import FILE_DIR
from sync import Package

# Set chunk size to 8 KB (8192 bytes)
chunk_size = 8192

# Create a package with filesystem storage and custom chunk size
print("Initializing package with 8 KB chunks...")
pkg = Package("large-package", 1, base_path=FILE_DIR, block_size=chunk_size)
print("Package initialized.\n")

# Generate a large file (50 MB)
file_path = "large_file.bin"
file_size = 50 * 1024 * 1024  # 50 MB in bytes

# Step 1: Create a large file filled with random data
print(f"Creating a {file_size // (1024 * 1024)} MB file...")
with open(file_path, "wb") as f:
    for i in range(file_size // chunk_size):
        f.write(b'\0' * chunk_size)  # Write zero-filled chunks
        if i % 100 == 0:  # Print progress every 100 chunks
            print(f"  Written {i * chunk_size // (1024 * 1024)} MB so far...")
print("File creation complete.\n")

# Step 2: Read the large file and write it as chunks into the package
print("Adding file to package as 8 KB chunks...")
with open(file_path, "rb") as f:
    block_number = 0
    while chunk := f.read(chunk_size):
        pkg.write_chunk("/downloads/large_file.bin", block_number, chunk, version=1)
        if block_number % 100 == 0:  # Print progress every 100 chunks
            print(f"  Processed {block_number * chunk_size // (1024 * 1024)} MB so far...")
        block_number += 1
print("File successfully added to package.")
print(f"Total chunks written: {block_number}")
