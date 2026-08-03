from pathlib import Path

CONTENT_DIR = Path("data/docs/content")

# grab a real page, skipping the small include snippets
pages = [f for f in CONTENT_DIR.rglob("*.md") if "includes/" not in f.as_posix()]
sample = pages[0]

text = sample.read_text(encoding="utf-8")

print("File:", sample.relative_to(CONTENT_DIR))
print("Length:", len(text), "characters")
print("=" * 60)
print(text[:1200])

