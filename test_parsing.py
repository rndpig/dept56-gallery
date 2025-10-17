from ingest_docx import read_docx_text, parse_metadata

# Test on a sample document
sample_path = r"\\DilgerNAS\Public\Media\Day NP Files\Elf Bunkhouse 1990.docx"
lines = read_docx_text(sample_path)

print("=== EXTRACTED TEXT (first 15 lines) ===")
for i, line in enumerate(lines[:15], 1):
    print(f"{i:2d}: {line}")

print("\n=== METADATA PARSING ===")
metadata = parse_metadata(lines)
print(f"Primary Title: {metadata['primary_title']}")
print(f"Accessory Titles: {metadata['accessory_titles']}")
print(f"All Titles: {metadata['all_titles']}")
print(f"SKUs: {metadata['skus']}")
print(f"Introduced: {metadata['introduced_years']}")
print(f"Retired: {metadata['retired_years']}")
print(f"Prices: {metadata['prices']}")
