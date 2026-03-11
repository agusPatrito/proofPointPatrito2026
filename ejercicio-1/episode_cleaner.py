
import csv
import re
import sys
import os
from datetime import datetime
from typing import Any
from helpers import parse_date, parse_int, clean_text, normalize


def read_and_clean(filepath):
    """
    Read the CSV at *filepath* and return:
      - records : list[dict]  cleaned, valid rows
      - stats   : dict        counters for the quality report
    """
    stats: dict[str, Any] = {
        "total_input": 0,
        "discarded": 0,
        "corrected": 0,
        "duplicates": 0,
        "corrections_detail": [],
    }

    records = []

    # Read with utf-8-sig to handle BOM
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        #Clean column names
        fieldnames = reader.fieldnames
        if fieldnames is not None:
            reader.fieldnames = [fn.strip() for fn in fieldnames]

        for row_num, row in enumerate(reader, start=2): # 2 because header(episode name, episode number, etc) is row 1 
            stats["total_input"] += 1
            corrections = [] 

            # Clean Series Name
            series = clean_text(row.get("SeriesName", "") or row.get("Series Name", "") or "")
            if not series:
                stats["discarded"] += 1
                stats["corrections_detail"].append(
                    f"Row {row_num}: Discarded — missing Series Name."
                )
                continue

            # Clean Season Number
            raw_season = (row.get("SeasonNumber", "") or row.get("Season Number", "") or "").strip()
            season = parse_int(raw_season)
            if raw_season and str(season) != raw_season:
                corrections.append("Season Number corrected")

            #Clean Episode Number
            raw_episode = (row.get("EpisodeNumber", "") or row.get("Episode Number", "") or "").strip()
            episode = parse_int(raw_episode)
            if raw_episode and str(episode) != raw_episode:
                corrections.append("Episode Number corrected")

            #Clean Episode Title
            title = clean_text(row.get("EpisodeTitle", "") or row.get("Episode Title", "") or "")
            title_is_missing = not title
            if title_is_missing:
                title = "Untitled Episode"
                corrections.append("Episode Title set to default")


            raw_date = (row.get("AirDate", "") or row.get("Air Date", "") or "").strip()
            air_date = parse_date(raw_date)
            date_is_missing = air_date == "Unknown"
            if raw_date and date_is_missing:
                corrections.append("Air Date invalid, set to Unknown")
            elif not raw_date:
                corrections.append("Air Date missing, set to Unknown")

            # Discard if Episode Number, Title AND Air Date are all missing.
            episode_missing = episode == 0
            if episode_missing and title_is_missing and date_is_missing:
                stats["discarded"] += 1
                stats["corrections_detail"].append(
                    f"Row {row_num}: Discarded — Episode Number, Episode Title, and Air Date all missing."
                )
                continue

            if corrections:
                stats["corrected"] += 1
                stats["corrections_detail"].append(
                    f"Row {row_num}: {'; '.join(corrections)}."
                )

            records.append({
                "SeriesName": series,
                "SeasonNumber": season,
                "EpisodeNumber": episode,
                "EpisodeTitle": title,
                "AirDate": air_date,
                "_row_num": row_num,    
            })

    return records, stats


def _score(rec):
    return (
        0 if rec["AirDate"] == "Unknown" else 1,
        0 if rec["EpisodeTitle"] == "Untitled Episode" else 1,
        (1 if rec["SeasonNumber"] > 0 else 0) + (1 if rec["EpisodeNumber"] > 0 else 0),
        -rec["_row_num"],
    )


def deduplicate(records, stats):
    buckets: dict[tuple, dict] = {}

    for rec in records:
        series_name_norm = normalize(rec["SeriesName"])
        episode_title_norm = normalize(rec["EpisodeTitle"])
        season = rec["SeasonNumber"]
        episode_number = rec["EpisodeNumber"]

        #Id each episode considering whether it has season 0 or episode 0.

        if season > 0 and episode_number > 0:
            key = (series_name_norm, season, episode_number)
        elif season == 0 and episode_number > 0:
            key = (series_name_norm, 0, episode_number, episode_title_norm)
        elif episode_number == 0 and season > 0:
            key = (series_name_norm, season, 0, episode_title_norm)
        else:
            key = (series_name_norm, 0, 0, episode_title_norm)

        #Compare them to select which one is better
        if key in buckets:
            existing = buckets[key]
            if _score(rec) > _score(existing):
                buckets[key] = rec
            stats["duplicates"] += 1
        else:
            buckets[key] = rec

    return list(buckets.values())


def sort_records(records):
    #Sorts based on name, if same, based on season number and if same, based on episode number.
    return sorted(
        records,
        key = lambda r: (normalize(r["SeriesName"]), r["SeasonNumber"], r["EpisodeNumber"])
        
    )


FIELDNAMES = ["SeriesName", "SeasonNumber", "EpisodeNumber", "EpisodeTitle", "AirDate"]


def write_clean_csv(records: list, out_path: str):
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def write_report(stats: dict[str, Any], out_path: str):
    total_input = stats["total_input"]
    duplicates = stats["duplicates"]
    discarded = stats["discarded"]
    corrected = stats["corrected"]
    total_output = total_input - discarded - duplicates

    lines = [
        "# Data Quality Report",

    ]

    if stats["corrections_detail"]:
        for detail in stats["corrections_detail"]:
            lines.append(f"- {detail}")
    else:
        lines.append("No corrections were necessary.")

    lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))



def main():
    if len(sys.argv) < 2:
        print("Usage: python episode_cleaner.py <input.csv>")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"Error: file '{input_path}' not found.")
        sys.exit(1)

    out_dir = os.path.dirname(os.path.abspath(input_path))
    clean_csv_path = os.path.join(out_dir, "episodes_clean.csv")
    report_path = os.path.join(out_dir, "report.md")

    print(f"Reading {input_path} ...")
    records, stats = read_and_clean(input_path)
    print(f"  {stats['total_input']} input records read.")
    print(f"  {stats['discarded']} discarded, {stats['corrected']} corrected.")

    print("Deduplicating ...")
    records = deduplicate(records, stats)
    print(f"  {stats['duplicates']} duplicates removed.")

    records = sort_records(records)

    write_clean_csv(records, clean_csv_path)
    print(f"Wrote {len(records)} records -> {clean_csv_path}")

    write_report(stats, report_path)
    print(f"Wrote quality report -> {report_path}")

    print("Done.")


if __name__ == "__main__":
    main()
