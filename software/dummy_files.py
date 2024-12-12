from config import FILE_DIR
from sync import Package

# Create a package with filesystem storage
pkg = Package("my-package", 1, base_path=FILE_DIR)

# Add chunks to files (automatically stored in filesystem)
pkg.write_chunk("/downloads/file1.txt", 0, b"Hello World", version=1)
pkg.write_chunk("/downloads/file2.txt", 0, b"Some data", version=1)

# Update a chunk with a new version (stored in filesystem)
pkg.write_chunk("/downloads/file1.txt", 0, b"Updated content", version=2)

# Later, reload the package from filesystem
reloaded_pkg = Package("my-package", 1, base_path=FILE_DIR)
reloaded_pkg.load_from_filesystem()
print(reloaded_pkg.read_chunk("/downloads/file1.txt", 0))
