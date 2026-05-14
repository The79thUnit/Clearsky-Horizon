"""Re-run text extraction on existing records.

For every case_report missing serotype_id/serotype_text or country_iso2,
re-run detect_serotype + detect_country + extract_region against the
current title + summary. Update the record if extraction now succeeds.

Idempotent and safe to re-run after every expansion of the heuristics
in text_utils. Also safe to schedule on a cadence.
"""

from __future__ import annotations

import json
import logging

from ..connectors.text_utils import (
    detect_country,
    detect_serotype,
    extract_region,
)
from ..db import get_conn

logger = logging.getLogger(__name__)


def main() -> dict[str, int]:
    examined = 0
    set_serotype = 0
    set_country = 0
    set_region = 0

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cr.id, cr.title, cr.summary,
                       cr.country_iso2, cr.region, cr.serotype_id, cr.serotype_text
                FROM case_reports cr
                """
            )
            rows = cur.fetchall()

            logger.info("backfill_text: examining %d records", len(rows))

            # Pre-load serotype id lookup
            cur.execute("SELECT id, code FROM serotypes")
            serotype_id_by_code = {r["code"]: r["id"] for r in cur.fetchall()}

            for row in rows:
                examined += 1
                haystack = f"{row['title']} {row.get('summary') or ''}"

                updates: dict[str, object] = {}

                if row["serotype_id"] is None and row["serotype_text"] is None:
                    # Pass existing country_iso2 so geographic inference can
                    # kick in for news records that already have a country but
                    # no explicit serotype keyword.
                    existing_country = row.get("country_iso2")
                    if existing_country:
                        existing_country = existing_country.strip()
                    sero = detect_serotype(haystack, country_iso2=existing_country)
                    if sero:
                        sero_id = serotype_id_by_code.get(sero)
                        updates["serotype_id"] = sero_id
                        updates["serotype_text"] = sero
                        set_serotype += 1

                if not row["country_iso2"]:
                    country = detect_country(haystack)
                    if country:
                        updates["country_iso2"] = country
                        set_country += 1

                if not row["region"]:
                    region = extract_region(row["title"])
                    if region:
                        updates["region"] = region
                        set_region += 1

                if not updates:
                    continue

                set_clauses = ", ".join(f"{k} = %s" for k in updates)
                values = list(updates.values())
                values.append(row["id"])
                cur.execute(
                    f"UPDATE case_reports SET {set_clauses} WHERE id = %s",
                    values,
                )

        conn.commit()

    summary = {
        "examined": examined,
        "set_serotype": set_serotype,
        "set_country": set_country,
        "set_region": set_region,
    }
    logger.info("backfill_text complete: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = main()
    print(json.dumps(result, indent=2))
