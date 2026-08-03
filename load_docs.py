from pathlib import Path

CONTENT_DIR = Path("data/docs/content")

md_files = list(CONTENT_DIR.rglob("*.md"))

total_bytes = sum(f.stat().st_size for f in md_files)

print(f"Found {len(md_files)} markdown files")
print(f"Total size: {total_bytes / 1_000_000:.1f} MB")
print("\nSample files:")
for f in md_files[:5]:
    print(f" - {f.relative_to(CONTENT_DIR)}")