#!/usr/bin/env python3
"""
RTF to CSV Converter for MedCAT Trainer
Converts a directory of RTF clinical documents to a CSV file for upload.

Usage:
    python rtf_to_csv_converter.py /path/to/rtf/files output.csv
"""

import csv
import os
import sys
from pathlib import Path
from striprtf.striprtf import rtf_to_text


def convert_rtf_directory_to_csv(rtf_dir: str, output_csv: str) -> None:
    """
    Convert all RTF files in a directory to a single CSV file.

    Args:
        rtf_dir: Directory containing RTF files
        output_csv: Output CSV file path
    """
    rtf_dir_path = Path(rtf_dir)

    if not rtf_dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {rtf_dir}")

    # Find all RTF files
    rtf_files = list(rtf_dir_path.glob("*.rtf")) + list(rtf_dir_path.glob("*.RTF"))

    if not rtf_files:
        raise ValueError(f"No RTF files found in {rtf_dir}")

    print(f"Found {len(rtf_files)} RTF files")

    # Convert to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['name', 'text'])
        writer.writeheader()

        for rtf_file in sorted(rtf_files):
            print(f"Processing: {rtf_file.name}")

            try:
                # Read RTF file
                with open(rtf_file, 'r', encoding='utf-8', errors='ignore') as f:
                    rtf_content = f.read()

                # Extract plain text from RTF
                plain_text = rtf_to_text(rtf_content)

                # Clean whitespace
                plain_text = ' '.join(plain_text.split())

                # Write to CSV
                writer.writerow({
                    'name': rtf_file.stem,  # Filename without extension
                    'text': plain_text
                })

            except Exception as e:
                print(f"  ⚠️  Error processing {rtf_file.name}: {e}")
                continue

    print(f"\n✅ Conversion complete: {output_csv}")
    print(f"   {len(rtf_files)} documents converted")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python rtf_to_csv_converter.py <rtf_directory> <output_csv>")
        print("\nExample:")
        print("  python rtf_to_csv_converter.py /mnt/clinical_notes output.csv")
        sys.exit(1)

    rtf_directory = sys.argv[1]
    output_file = sys.argv[2]

    convert_rtf_directory_to_csv(rtf_directory, output_file)
