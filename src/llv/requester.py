import re
import requests
import json
import csv

# Quelle: Bank $8F Logs von PJBoy
ASM_URL = (
    "https://raw.githubusercontent.com/"
    "yuriks/pjboy-sm-bank-logs/main/Bank%20%248F.asm"
)

# Optional: Mapping PLM-ID -> lesbarer Name
PLM_NAMES = {
    "EF23": "morph_ball",
    # Füge hier weitere IDs hinzu
}


def lorom_to_file_offset(bank: int, addr: int) -> int:
    """
    SNES LoROM → Datei-Offset
    Bank 0x80–0xFF liegen in 0x8000-Byte-Blöcken,
    niedrigste 15 Bit der Adresse sind der Block-Offset.
    """
    return ((bank & 0x7F) << 15) | (addr & 0x7FFF)


def parse_bank_8f(asm_text: str) -> list:
    """
    Parst die Bank $8F.asm und erzeugt für jeden Raum eine Struktur mit:
      - description: Kommentarzeile über der PLM-Liste
      - base_lorom: LoROM-Adresse
      - base_file_offset: entsprechender Datei-Offset
      - plms: Liste von PLM-Einträgen mit Feldern id, x, y, param, file_offset, description, name
    """
    lines = asm_text.splitlines()
    level_map = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        # Detect PLM-list start: a dx directive in Bank $8F
        if stripped.startswith('$8F:') and 'dx' in stripped:
            # Beschreibung aus vorheriger Zeile, wenn Kommentar
            prev = lines[i-1].strip() if i > 0 else ''
            desc = prev if prev.startswith(';') else ''
            # Basis-LoROM-Adresse
            off_match = re.search(r'\$8F:([0-9A-Fa-f]{4})', stripped)
            bank_off = int(off_match.group(1), 16)
            base_lorom = f"8F:{off_match.group(1).upper()}"
            base_file = lorom_to_file_offset(0x8F, bank_off)

            # Sammle PLM-Block: ab 'dx' bis Terminator
            block_lines = []
            # erste Zeile nach 'dx'
            first = stripped.split('dx', 1)[1].strip()
            block_lines.append(first)
            # folgende Zeilen bis '0000'
            j = i + 1
            while j < len(lines):
                line_j = lines[j].strip()
                block_lines.append(line_j)
                if line_j.startswith('0000'):
                    break
                j += 1

            # PLM-Einträge parsen
            plms = []
            for idx, entry in enumerate(block_lines):
                # Match only lines with ID, X, Y, Param, ; Description
                m = re.match(
                    r'^([0-9A-Fa-f]{4})\s*,\s*([0-9A-Fa-f]{2})\s*,\s*'
                    r'([0-9A-Fa-f]{2})\s*,\s*([0-9A-Fa-f]{4}),\s*;\s*(.+)$',
                    entry
                )
                if not m:
                    continue
                id_hex, x_hex, y_hex, p_hex, comment = m.groups()
                id_hex = id_hex.upper()
                file_off = base_file + idx * 6
                plms.append({
                    'id':            id_hex,
                    'x':             int(x_hex, 16),
                    'y':             int(y_hex, 16),
                    'param':         p_hex.upper(),
                    'file_offset':   f"{file_off:06X}",
                    'description':   comment.strip(),
                    'name':          PLM_NAMES.get(id_hex, '')
                })

            level_map.append({
                'description':      desc,
                'base_lorom':       base_lorom,
                'base_file_offset': f"{base_file:06X}",
                'plms':             plms
            })
    return level_map


if __name__ == '__main__':
    # ASM herunterladen
    resp = requests.get(ASM_URL)
    resp.raise_for_status()
    asm = resp.text

    # Parsen und speichern
    levels = parse_bank_8f(asm)

    # JSON speichern
    with open('level_map.json', 'w', encoding='utf-8') as f:
        json.dump(levels, f, indent=2, ensure_ascii=False)
    print('→ level_map.json erstellt')

    # CSV speichern
    with open('level_map.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'description', 'base_lorom', 'base_file_offset',
            'plm_id', 'plm_name', 'x', 'y', 'param', 'file_offset', 'plm_description'
        ])
        for lvl in levels:
            for p in lvl['plms']:
                writer.writerow([
                    lvl['description'], lvl['base_lorom'], lvl['base_file_offset'],
                    p['id'], p['name'], p['x'], p['y'], p['param'], p['file_offset'], p['description']
                ])
    print('→ level_map.csv erstellt')