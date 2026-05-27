import csv
from pathlib import Path


def read_csv_file(csv_path: str) -> tuple[list[dict], list[str]]:
    """Read tab-delimited CSV into list of dicts."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames or []
        for row in reader:
            rows.append(dict(row))
    return rows, list(headers)

def write_csv_file(csv_path: str, rows: list[dict], headers: list[str] = None):
    """Write list of dicts to tab-delimited CSV."""
    fieldnames = headers
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            clean_row = {h: row.get(h, "") for h in fieldnames}
            writer.writerow(clean_row)


def read_trade_xmls(trades_dir: str) -> dict[str, str]:
    """Read all XML files from trades directory. Returns {filename: content}."""
    xmls = {}
    trades_path = Path(trades_dir)
    if trades_path.exists():
        for xml_file in sorted(trades_path.glob("*.xml")):
            xmls[xml_file.name] = xml_file.read_text(encoding="utf-8")
    return xmls


def write_trade_xml(trades_dir: str, filename: str, content: str):
    """Write a single XML trade file."""
    filepath = Path(trades_dir) / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"  Written XML: {filepath}")


def delete_trade_xml(trades_dir: str, filename: str):
    """Delete a single XML trade file."""
    filepath = Path(trades_dir) / filename
    if filepath.exists():
        filepath.unlink()
        print(f"  Deleted XML: {filepath}")