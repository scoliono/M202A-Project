from config import FILE_DIR
from sync import Package

# Set chunk size to 1 MB (1048576 bytes)
chunk_size = 1 * 1024 * 1024  # 1 MB

# Create a package with filesystem storage and custom chunk size
print("Initializing package with 1 MB chunks...")
pkg = Package("large-package", 1, base_path=FILE_DIR)
print("Package initialized.\n")

# Generate a large file (256 MB)
file_path = "large_file.bin"
file_size = 256 * 1024 * 1024  # 256 MB in bytes

# Step 1: Create a large file filled with random data
print(f"Creating a {file_size // (1024 * 1024)} MB file...")
with open(file_path, "wb") as f:
    for i in range(file_size // chunk_size):
        f.write(b'\0' * chunk_size)  # Write zero-filled chunks
        if i % 10 == 0:  # Print progress every 10 chunks (10 MB progress)
            print(f"  Written {i * chunk_size // (1024 * 1024)} MB so far...")
print("File creation complete.\n")

# Step 2: Read the large file and write it as chunks into the package
print("Adding file to package as 1 MB chunks...")
with open(file_path, "rb") as f:
    block_number = 0
    while chunk := f.read(chunk_size):
        pkg.write_chunk("/downloads/large_file.bin", block_number, chunk, version=1)
        if block_number % 10 == 0:  # Print progress every 10 chunks (10 MB progress)
            print(f"  Processed {block_number * chunk_size // (1024 * 1024)} MB so far...")
        block_number += 1
print("File successfully added to package.")
print(f"Total chunks written: {block_number}")
