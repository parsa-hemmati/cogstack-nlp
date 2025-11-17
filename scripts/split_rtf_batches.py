#!/usr/bin/env python3
"""
Split large RTF dataset into overlapping batches for multi-clinician validation.

Usage:
    python split_rtf_batches.py /path/to/rtf/files /path/to/output --num-batches 5 --overlap 500
"""

import argparse
import csv
import os
import shutil
from pathlib import Path
from typing import List, Tuple
from striprtf.striprtf import rtf_to_text


def get_sorted_rtf_files(rtf_dir: Path) -> List[Path]:
    """Get all RTF files sorted alphabetically."""
    rtf_files = list(rtf_dir.glob("*.rtf")) + list(rtf_dir.glob("*.RTF"))
    return sorted(rtf_files)


def calculate_batch_ranges(total_docs: int, num_batches: int, overlap: int) -> List[Tuple[int, int]]:
    """
    Calculate start/end indices for each batch with overlap.

    Args:
        total_docs: Total number of documents
        num_batches: Number of batches to create
        overlap: Number of overlapping documents between adjacent batches

    Returns:
        List of (start_idx, end_idx) tuples for each batch
    """
    if num_batches <= 0:
        raise ValueError("num_batches must be positive")

    if overlap < 0:
        raise ValueError("overlap must be non-negative")

    # Calculate batch size (with overlap)
    # Total coverage with overlap: total_docs = (num_batches * batch_size) - ((num_batches - 1) * overlap)
    # Solve for batch_size: batch_size = (total_docs + (num_batches - 1) * overlap) / num_batches
    batch_size = (total_docs + (num_batches - 1) * overlap) // num_batches

    batches = []
    start_idx = 0

    for i in range(num_batches):
        if i == num_batches - 1:
            # Last batch: include remaining documents
            end_idx = total_docs
        else:
            end_idx = start_idx + batch_size

        batches.append((start_idx, end_idx))

        # Next batch starts (overlap) documents before current batch ends
        start_idx = end_idx - overlap

    return batches


def convert_rtf_to_text(rtf_file: Path) -> str:
    """Convert RTF file to plain text."""
    try:
        with open(rtf_file, 'r', encoding='utf-8', errors='ignore') as f:
            rtf_content = f.read()

        plain_text = rtf_to_text(rtf_content)
        # Clean whitespace
        plain_text = ' '.join(plain_text.split())
        return plain_text
    except Exception as e:
        print(f"  ⚠️  Error converting {rtf_file.name}: {e}")
        return ""


def create_batch_csv(rtf_files: List[Path], batch_name: str, output_dir: Path):
    """Create CSV file for a batch of RTF documents."""
    csv_path = output_dir / f"{batch_name}.csv"

    print(f"\nCreating {batch_name}.csv ({len(rtf_files)} documents)...")

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['name', 'text'])
        writer.writeheader()

        for rtf_file in rtf_files:
            print(f"  Processing: {rtf_file.name}")
            plain_text = convert_rtf_to_text(rtf_file)

            if plain_text:
                writer.writerow({
                    'name': rtf_file.stem,
                    'text': plain_text
                })

    print(f"✅ Created: {csv_path} ({len(rtf_files)} documents)")


def main():
    parser = argparse.ArgumentParser(
        description='Split RTF documents into overlapping batches for multi-clinician validation'
    )
    parser.add_argument('rtf_dir', type=str, help='Directory containing RTF files')
    parser.add_argument('output_dir', type=str, help='Output directory for CSV batches')
    parser.add_argument('--num-batches', type=int, default=5, help='Number of batches to create (default: 5)')
    parser.add_argument('--overlap', type=int, default=500, help='Number of overlapping documents between batches (default: 500)')
    parser.add_argument('--batch-prefix', type=str, default='batch', help='Prefix for batch filenames (default: "batch")')

    args = parser.parse_args()

    rtf_dir = Path(args.rtf_dir)
    output_dir = Path(args.output_dir)

    # Validate inputs
    if not rtf_dir.exists():
        raise FileNotFoundError(f"RTF directory not found: {rtf_dir}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all RTF files
    rtf_files = get_sorted_rtf_files(rtf_dir)
    total_docs = len(rtf_files)

    if total_docs == 0:
        raise ValueError(f"No RTF files found in {rtf_dir}")

    print(f"Found {total_docs} RTF files")
    print(f"Creating {args.num_batches} batches with {args.overlap} overlapping documents\n")

    # Calculate batch ranges
    batch_ranges = calculate_batch_ranges(total_docs, args.num_batches, args.overlap)

    # Display batch allocation
    print("Batch Allocation:")
    print("-" * 60)
    total_overlap_docs = 0

    for i, (start_idx, end_idx) in enumerate(batch_ranges):
        batch_size = end_idx - start_idx
        batch_label = chr(65 + i)  # A, B, C, D, E...

        # Calculate overlap with previous batch
        if i > 0:
            prev_end = batch_ranges[i-1][1]
            overlap_docs = prev_end - start_idx
            total_overlap_docs += overlap_docs
            overlap_str = f"(overlap: {overlap_docs} docs with Batch {chr(65 + i - 1)})"
        else:
            overlap_str = ""

        print(f"Batch {batch_label}: Documents {start_idx + 1:5d} - {end_idx:5d} "
              f"({batch_size:4d} docs) {overlap_str}")

    print("-" * 60)
    print(f"Total unique documents: {total_docs}")
    print(f"Total overlap documents: {total_overlap_docs}")
    print(f"Total validations: {total_docs + total_overlap_docs} "
          f"({(total_overlap_docs / total_docs * 100):.1f}% overlap rate)\n")

    # Create CSV batches
    for i, (start_idx, end_idx) in enumerate(batch_ranges):
        batch_label = chr(65 + i)  # A, B, C, D, E...
        batch_name = f"{args.batch_prefix}_{batch_label}"
        batch_files = rtf_files[start_idx:end_idx]

        create_batch_csv(batch_files, batch_name, output_dir)

    print(f"\n✅ All batches created in: {output_dir}")
    print(f"\nNext steps:")
    print(f"1. Upload each CSV to MedCAT Trainer as a separate Dataset")
    print(f"2. Create ProjectAnnotateEntities for each batch")
    print(f"3. Assign clinicians to their respective projects")


if __name__ == "__main__":
    main()
