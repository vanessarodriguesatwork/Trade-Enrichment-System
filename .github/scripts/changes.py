from file_io import write_trade_xml, delete_trade_xml


def apply_csv_changes(
    csv_rows: list[dict],
    changes: list[dict],
    new_columns: list[dict],
    current_headers: list[str] = None,
) -> tuple[list[dict], list[str]]:
    """Apply modify/insert/delete changes to CSV rows.

    Returns (updated_rows, updated_headers).
    """
    headers = list(current_headers) 

    # ── Extend headers for any new columns ──
    for col in new_columns:
        if col["name"] not in headers:
            # Insert new output columns just before expected_output
            headers.insert(headers.index("expected_output"), col["name"])
            print(f"  New column added: {col['name']} — {col['reason']}")

    # ── Backfill new columns in existing rows ──
    for row in csv_rows:
        for col in new_columns:
            if col["name"] not in row:
                row[col["name"]] = ""

    # ── Index existing rows by scenario_id ──
    row_index = {row["scenario_id"]: i for i, row in enumerate(csv_rows)}

    rows_to_delete = set()
    rows_to_insert = []

    for change in changes:
        action = change["action"]
        scenario_id = change.get("scenario_id", "")
        reason = change.get("reason", "")

        if action == "modify":
            if scenario_id in row_index:
                csv_rows[row_index[scenario_id]] = change["row"]
                print(f"  Modified: {scenario_id} — {reason}")
            else:
                print(f"  WARNING: Cannot modify {scenario_id} — not found, inserting instead")
                rows_to_insert.append(change["row"])

        elif action == "insert":
            rows_to_insert.append(change["row"])
            print(f"  Inserted: {scenario_id} — {reason}")

        elif action == "delete":
            if scenario_id in row_index:
                rows_to_delete.add(scenario_id)
                print(f"  Deleted: {scenario_id} — {reason}")
            else:
                print(f"  WARNING: Cannot delete {scenario_id} — not found")

    csv_rows = [row for row in csv_rows if row.get("scenario_id") not in rows_to_delete]
    csv_rows.extend(rows_to_insert)

    def sort_key(row):
        sid = row.get("scenario_id", "")
        try:
            return int(sid.replace("TC-", ""))
        except ValueError:
            return 9999

    csv_rows.sort(key=sort_key)
    return csv_rows, headers


def apply_xml_changes(trades_dir: str, changes: list[dict]):
    """Apply create/modify/delete changes to XML trade files."""
    for change in changes:
        action = change["action"]
        filename = change["filename"]
        content = change.get("content", "")
        reason = change.get("reason", "")

        if action in ("create", "modify"):
            write_trade_xml(trades_dir, filename, content)
            print(f"  {'Created' if action == 'create' else 'Modified'}: {filename} — {reason}")
        elif action == "delete":
            delete_trade_xml(trades_dir, filename)
            print(f"  Deleted: {filename} — {reason}")