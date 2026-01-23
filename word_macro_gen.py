#!/usr/bin/env python3
"""
Word Frequency Macro Generator for ZMK
Analyzes text files and generates keyboard macro combinations
"""

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import List, Tuple, Dict, Set
import argparse

# Keyboard layout mapping based on Corne/Sweep layout
LAYOUT = {
    'LN5': 'TAB', 'LN4': 'Q', 'LN3': 'W', 'LN2': 'E', 'LN1': 'R', 'LN0': 'T',
    'LT5': 'ESC', 'LT4': 'A', 'LT3': 'S', 'LT2': 'D', 'LT1': 'F', 'LT0': 'G',
    'LM5': 'NUBS', 'LM4': 'Z', 'LM3': 'X', 'LM2': 'C', 'LM1': 'V', 'LM0': 'B',
    'RN0': 'Y', 'RN1': 'U', 'RN2': 'I', 'RN3': 'O', 'RN4': 'P', 'RN5': 'BSPC',
    'RT0': 'H', 'RT1': 'J', 'RT2': 'K', 'RT3': 'L', 'RT4': 'SEMI', 'RT5': 'SQT',
    'RM0': 'N', 'RM1': 'M', 'RM2': 'COMMA', 'RM3': 'DOT', 'RM4': 'FSLH', 'RM5': 'LBKT',
    'LH1': 'SHIFT', 'LH0': 'RET',
    'RH0': 'SPC', 'RH1': 'NUM'
}

# Finger assignment for each key position
FINGER_MAP = {
    'LN5': 'L_pinky', 'LN4': 'L_ring', 'LN3': 'L_middle', 'LN2': 'L_index', 'LN1': 'L_index', 'LN0': 'L_index',
    'LT5': 'L_pinky', 'LT4': 'L_ring', 'LT3': 'L_middle', 'LT2': 'L_index', 'LT1': 'L_index', 'LT0': 'L_index',
    'LM5': 'L_pinky', 'LM4': 'L_ring', 'LM3': 'L_middle', 'LM2': 'L_index', 'LM1': 'L_index', 'LM0': 'L_index',
    'RN0': 'R_index', 'RN1': 'R_index', 'RN2': 'R_index', 'RN3': 'R_middle', 'RN4': 'R_ring', 'RN5': 'R_pinky',
    'RT0': 'R_index', 'RT1': 'R_index', 'RT2': 'R_index', 'RT3': 'R_middle', 'RT4': 'R_ring', 'RT5': 'R_pinky',
    'RM0': 'R_index', 'RM1': 'R_index', 'RM2': 'R_index', 'RM3': 'R_middle', 'RM4': 'R_ring', 'RM5': 'R_pinky',
    'LH1': 'L_thumb', 'LH0': 'L_thumb',
    'RH0': 'R_thumb', 'RH1': 'R_thumb'
}

# Reverse mapping: letter to key positions
LETTER_TO_POSITIONS = {}
for pos, key in LAYOUT.items():
    if len(key) == 1 and key.isalpha():
        LETTER_TO_POSITIONS[key.upper()] = pos


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', pdf_path, '-'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        print(f"Warning: Failed to extract text from {pdf_path}", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("Error: pdftotext not found. Please install poppler-utils.", file=sys.stderr)
        sys.exit(1)


def read_file_content(file_path: str) -> str:
    """Read content from text, markdown, or PDF files."""
    path = Path(file_path)
    
    if path.suffix.lower() == '.pdf':
        return extract_text_from_pdf(file_path)
    else:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Failed to read {file_path}: {e}", file=sys.stderr)
            return ""


def process_directory(directory: str) -> Counter:
    """Process all text/markdown/PDF files in a directory."""
    word_counter = Counter()
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.txt', '.md', '.tex', '.pdf')):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                
                content = read_file_content(file_path)
                # Extract words (alphanumeric sequences)
                words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
                word_counter.update(words)
    
    return word_counter


def calculate_weighted_score(word: str, frequency: int) -> float:
    """Calculate weighted score: frequency * word_length."""
    return frequency * len(word)


def get_key_positions_for_word(word: str) -> List[str]:
    """Get key positions for each letter in a word."""
    positions = []
    for char in word.upper():
        if char in LETTER_TO_POSITIONS:
            positions.append(LETTER_TO_POSITIONS[char])
        else:
            return []  # Can't map this word
    return positions


def check_one_key_per_finger(positions: List[str]) -> bool:
    """Check if each finger is responsible for only one key."""
    fingers_used = set()
    for pos in positions:
        finger = FINGER_MAP.get(pos)
        if not finger:
            return False
        if finger in fingers_used:
            return False  # Same finger used twice
        fingers_used.add(finger)
    return True


def is_valid_combo(word: str, positions: List[str], used_combos: Set[frozenset]) -> bool:
    """Check if a combo is valid and doesn't clash with existing ones."""
    if len(positions) < 3:
        return False
    if len(word) < 4:
        return False
    if not check_one_key_per_finger(positions):
        return False
    
    # Check for clash with existing combos
    combo_set = frozenset(positions)
    if combo_set in used_combos:
        return False
    
    return True


def generate_zmk_combo(word: str, positions: List[str]) -> str:
    """Generate ZMK_COMBO macro string."""
    # Create the binding part (spell out the word)
    bindings = ' '.join([f'&kp {LAYOUT[pos]}' for pos in positions])
    
    # Create the position part
    pos_str = ' '.join(positions)
    
    # Sanitize word for macro name
    macro_name = f"macro_{word.replace('-', '_')}"
    
    return f"ZMK_COMBO({macro_name},  <{bindings}>,     {pos_str},     ALL, COMBO_TERM_SLOW, COMBO_IDLE_SLOW)"


def main():
    parser = argparse.ArgumentParser(
        description='Generate ZMK macros from word frequency analysis'
    )
    parser.add_argument('directory', help='Directory containing text files')
    parser.add_argument('-o', '--output', default='macros.txt',
                        help='Output file for macros (default: macros.txt)')
    parser.add_argument('-n', '--num-words', type=int, default=100,
                        help='Number of top words to process (default: 100)')
    parser.add_argument('--csv', default='word_analysis.csv',
                        help='CSV output file (default: word_analysis.csv)')
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing files in: {args.directory}")
    word_counter = process_directory(args.directory)
    
    if not word_counter:
        print("No words found in the specified directory.", file=sys.stderr)
        sys.exit(1)
    
    # Calculate weighted scores
    scored_words = [
        (word, freq, calculate_weighted_score(word, freq))
        for word, freq in word_counter.items()
    ]
    
    # Sort by weighted score (descending)
    scored_words.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\nTotal unique words: {len(scored_words)}")
    print(f"Processing top {args.num_words} words...")
    
    # Generate macros
    used_combos = set()
    valid_macros = []
    
    for word, freq, score in scored_words[:args.num_words]:
        positions = get_key_positions_for_word(word)
        
        if positions and is_valid_combo(word, positions, used_combos):
            combo_set = frozenset(positions)
            used_combos.add(combo_set)
            
            # Format: shortcut letters, key positions, word
            shortcut = word.upper()
            keys = ' '.join(positions)
            valid_macros.append((shortcut, keys, word, freq, score))
    
    # Write CSV output
    with open(args.csv, 'w') as f:
        f.write("Shortcut,Keys,Word,Frequency,Score\n")
        for shortcut, keys, word, freq, score in valid_macros:
            f.write(f'"{shortcut}","{keys}","{word}",{freq},{score}\n')
    
    print(f"Word analysis saved to: {args.csv}")
    
    # Write ZMK macros
    with open(args.output, 'w') as f:
        f.write("// Auto-generated ZMK combos for frequent words\n")
        f.write("// Generated by Word Frequency Macro Generator\n\n")
        
        for shortcut, keys, word, _, _ in valid_macros:
            positions = keys.split()
            zmk_line = generate_zmk_combo(word, positions)
            f.write(f"{zmk_line}\n")
    
    print(f"ZMK macros saved to: {args.output}")
    print(f"Generated {len(valid_macros)} valid macros")
    
    # Print top 10
    print("\nTop 10 words by weighted score:")
    for i, (shortcut, keys, word, freq, score) in enumerate(valid_macros[:10], 1):
        print(f"{i}. {word:15} (freq: {freq:4}, score: {score:6.0f})")


if __name__ == '__main__':
    main()
