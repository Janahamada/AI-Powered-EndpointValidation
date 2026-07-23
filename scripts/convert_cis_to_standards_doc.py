"""
One-time (or re-run-on-update) conversion: reads the CIS Controls
spreadsheet and writes a plain-text doc into policies/standards/, with
one blank-line-separated paragraph per control/safeguard — matching the
paragraph-level chunking rag/vector_store.py already does, so each CIS
item becomes its own retrievable chunk.

Usage:
    python scripts/convert_cis_to_standards_doc.py \
        --xlsx "CIS_Controls_Version_8_1_2___March_2025.xlsx" \
        --out policies/standards/cis_controls_v8_1_2.md
"""

import argparse
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]


def _normalize_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def resolve_input_path(raw_path: str) -> Path:
    candidate = Path(raw_path)

    if candidate.is_file():
        return candidate.resolve()

    repo_candidate = REPO_ROOT / candidate
    if repo_candidate.is_file():
        return repo_candidate.resolve()

    # Common convenience fallback for the CIS workbook stored under policies/standards.
    standards_candidate = REPO_ROOT / "policies" / "standards" / candidate.name
    if standards_candidate.is_file():
        return standards_candidate.resolve()

    wanted_key = _normalize_name(candidate.name)
    for workbook in REPO_ROOT.rglob("*.xlsx"):
        current_key = _normalize_name(workbook.name)
        if current_key == wanted_key or current_key.startswith(wanted_key) or wanted_key.startswith(current_key):
            return workbook.resolve()

    raise FileNotFoundError(
        f"Could not find workbook '{raw_path}'. "
        f"Looked in the current working directory, the repo root, and '{REPO_ROOT / 'policies' / 'standards'}'."
    )


def build_chunks(df: pd.DataFrame) -> list[str]:
    chunks = []
    for _, row in df.iterrows():
        title = row.get("Title")
        if pd.isna(title):
            continue  # skip any fully-blank row

        control = row.get("CIS Control")
        safeguard = row.get("CIS Safeguard")
        description = row.get("Description") if not pd.isna(row.get("Description")) else ""

        if pd.isna(safeguard):
            # Control-family summary row (e.g. "CIS Control 10: Malware Defenses") —
            # useful for broad "does this control category exist" queries.
            header = f"CIS Control {int(control)}: {title}"
        else:
            asset_class = row.get("Asset Class")
            security_function = row.get("Security Function")
            meta_bits = [b for b in (asset_class, security_function) if not pd.isna(b)]
            meta_line = f" ({' / '.join(meta_bits)})" if meta_bits else ""
            header = f"CIS Safeguard {safeguard}{meta_line}: {title}"

        chunks.append(f"{header}\n{description}".strip())

    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", required=True)
    parser.add_argument("--sheet", default="Controls v8.1.2")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    xlsx_path = resolve_input_path(args.xlsx)
    out_path = (REPO_ROOT / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(xlsx_path, sheet_name=args.sheet)
    chunks = build_chunks(df)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(chunks))

    print(f"Wrote {len(chunks)} CIS control/safeguard chunks to {out_path}")


if __name__ == "__main__":
    main()
