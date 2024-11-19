from sync import *

# Create a package
pkg = Package("my-package", 1)

# Add some chunks to files
pkg.write_chunk("/src/file1.txt", 0, b"Hello World", version=1)
pkg.write_chunk("/src/file2.txt", 0, b"Some data", version=1)

# Update a chunk with a new version
pkg.write_chunk("/src/file1.txt", 0, b"Updated content", version=2)
assert pkg.version == 2

# Get the package manifest
manifest = pkg.get_manifest()
print("pkg:\n", manifest)

# Save manifest to file
# pkg.save_manifest("package-manifest.json")

# Create another package and sync chunks
other_pkg = Package("my-package", 1)
print("other_pkg before sync:\n", other_pkg.get_manifest())

missing_chunks = other_pkg.get_missing_chunks(manifest)
other_pkg.sync_chunks(pkg, missing_chunks)

print("other_pkg after sync:\n", other_pkg.get_manifest())

print("validating other_pkg chunk 0")

assert other_pkg.read_chunk("/src/file1.txt", 0).startswith(b"Updated content")
assert len(other_pkg.read_chunk("/src/file1.txt", 0)) == 2048

print("tests passed")
