import sys
import re
from collections import OrderedDict

# === CONFIG ===
MIN_LEN = 8
UTF8_THRESHOLD = 0.85

def is_printable_utf8(s: str) -> bool:
    """Check if string is mostly printable and valid."""
    if len(s) < MIN_LEN:
        return False
    printable = sum(ch.isprintable() for ch in s)
    return printable / max(len(s), 1) >= UTF8_THRESHOLD

def extract_utf8_strings(data: bytes):
    """Extract null-terminated UTF-8 strings from binary."""
    results = []
    current = bytearray()
    for b in data:
        if b == 0x00:
            if len(current) >= MIN_LEN:
                try:
                    text = current.decode("utf-8", errors="strict")
                    if is_printable_utf8(text):
                        results.append(text)
                except:
                    pass
            current.clear()
        else:
            current.append(b)
    return results

def extract_utf16_le_strings(data: bytes):
    """Extract possible UTF-16 LE sequences."""
    results = []
    current = bytearray()

    i = 0
    while i < len(data) - 1:
        # Potential UTF-16 LE printable block
        if data[i+1] == 0x00:
            current.extend(data[i:i+2])
            i += 2
        else:
            if len(current) >= MIN_LEN * 2:
                try:
                    text = current.decode("utf-16-le")
                    if is_printable_utf8(text):
                        results.append(text)
                except:
                    pass
            current.clear()
            i += 1
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_subtitles.py <file.subtitles>")
        return

    file_path = sys.argv[1]
    with open(file_path, "rb") as f:
        data = f.read()

    print("[*] Extracting UTF-8 clear text…")
    utf8_strings = extract_utf8_strings(data)

    print("[*] Extracting UTF-16 LE candidate text…")
    utf16_strings = extract_utf16_le_strings(data)

    # Merge and dedupe while preserving order
    all_lines = list(OrderedDict.fromkeys(utf8_strings + utf16_strings))

    # Save all raw extracted
    with open("extracted_strings.txt", "w", encoding="utf-8") as out:
        for line in all_lines:
            out.write(line + "\n")

    # Simple cleanup for candidate subtitle lines
    pattern = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9\.,!\?]+")
    candidates = [line for line in all_lines if pattern.search(line)]

    with open("subtitle_candidates.txt", "w", encoding="utf-8") as sub_out:
        for line in candidates:
            sub_out.write(line + "\n")

    print(f"[+] Done! Candidates: {len(candidates)}")
    print("→ extracted_strings.txt")
    print("→ subtitle_candidates.txt")

if __name__ == "__main__":
    main()
