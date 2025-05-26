import os, sys, re
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QLabel,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from PySide6.QtGui import QFontDatabase, QTextCursor, QTextCharFormat, QColor

from llv_utility import dump_line
from llv_utility import hex_to_dec, dec_to_hex

class LoaderThread(QtCore.QThread):
    """Background loader that streams the file incrementally so the UI never blocks."""

    progress = QtCore.Signal(int)  # 0–100
    finished = QtCore.Signal(str, bytearray, str)  # hexdump string, raw bytes

    def __init__(self, path: str, bytes_per_line: int = 16, chunk_size: int = 256 * 1024):
        super().__init__()
        self._path = path
        self._bpl = bytes_per_line
        self._chunk = chunk_size

    # --------------------- worker thread ---------------------
    def run(self) -> None:
        file_size = os.path.getsize(self._path)
        emitted = -1  # limit signal spam

        data = bytearray()
        hexdump_parts: list[str] = []
        ascii_parts: list[str] = []
        addr = 0

        with open(self._path, "rb") as fp:
            while True:
                chunk = fp.read(self._chunk)
                if not chunk:
                    break  # EOF

                # accumulate raw data
                data.extend(chunk)

                # build hexdump lines – we do it here so the GUI thread stays lean
                for i in range(0, len(chunk), self._bpl):
                    sub = chunk[i : i + self._bpl]
                    line, a = dump_line(addr, sub, self._bpl)
                    ascii_parts.append(a)
                    hexdump_parts.append(line)
                    addr += len(sub)

                # emit progress only when it has actually advanced
                pct = int(len(data) * 100 / file_size) if file_size else 100
                if pct != emitted:
                    emitted = pct
                    self.progress.emit(pct)

        hexdump = "".join(hexdump_parts)
        if not hexdump.endswith("\n"):
            hexdump += "\n"
        
        aciidump = "".join(ascii_parts)

        self.finished.emit(hexdump, data, aciidump)


class FileDump(QtWidgets.QWidget):
    """Hex‑viewer / editor with search *and* address‑jump (e.g. “$0300”)."""

    bytes_per_line = 16  # visual layout as well as search math

    def __init__(self, argv=None):
        super().__init__()
        self.setWindowTitle("FileDump – hex viewer / editor")

        # state ------------------------------------------------------------
        self._raw: bytearray = bytearray()
        self._path: str | None = None
        self._modified: bool = False
        self.ascii_text : str | None = None
        self.pc_addr : str | None = "Empty not set"
        # UI ---------------------------------------------------------------
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._build_ui(), "Hex View")
        self.tabs.addTab(self.create_text_example(), "Hex View")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        #self._build_ui()

    # ------------------------------------------------------------------ UI helpers
    def _build_ui(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        root = QVBoxLayout()

        # file open / save --------------------------------------------------
        file_bar = QHBoxLayout()
        self.open_btn = QPushButton("Open…")
        self.save_btn = QPushButton("Save")
        self.CopyAscii_btn = QPushButton("Copy ASCII")
        self.save_btn.setEnabled(False)
        file_bar.addWidget(self.open_btn)
        file_bar.addWidget(self.save_btn)
        file_bar.addWidget(self.CopyAscii_btn)
        root.addLayout(file_bar)

        self.open_btn.clicked.connect(self._open_file)
        self.save_btn.clicked.connect(self._save_changes)
        self.CopyAscii_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.ascii_text or ""))

        # search / jump -----------------------------------------------------
        search_bar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Hex / ASCII search — or jump to $ADDR…")
        self.search_btn = QPushButton("Go")
        search_bar.addWidget(self.search_edit, 1)
        search_bar.addWidget(self.search_btn)
        root.addLayout(search_bar)

        self.search_btn.clicked.connect(self._do_search_or_jump)

        # progress ----------------------------------------------------------
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        # hex view ----------------------------------------------------------
        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        self.view.setFont(font)
        self.view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.view.cursorPositionChanged.connect(self._update_status_offset)
        self.view.textChanged.connect(self._mark_modified)
        root.addWidget(self.view, 1)

        # status ------------------------------------------------------------
        self.status = QLabel("Ready")
        root.addWidget(self.status)
        widget.setLayout(root)
        return widget
    
    def create_text_example(self):
        # Text Input Tab
        widget = QtWidgets.QWidget()
        layout = QVBoxLayout()

        # Line edit
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Full loROM address (e.g. 8486D0) or bank (e.g. 84)")
        layout.addWidget(self.line_edit)
        
        # Button to open file dialog
        self.open_button = QPushButton("Convert LoROM to PC")
        self.open_button.clicked.connect(lambda _: self._on_lorom_btn(self.line_edit.text()))
        layout.addWidget(self.open_button)

        self.lorom_text_box = QLabel()
        self.lorom_text_box.setText(self.pc_addr)
        self.lorom_text_box.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(self.lorom_text_box)

        widget.setLayout(layout)
        return widget

    # ------------------------------------------------------------------ File handling
    def _open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose binary file", "", "All Files (*)")
        if not file_path:
            return

        self._path = file_path
        self.view.clear()
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status.setText("Loading…")
        self.view.setReadOnly(True)

        # kick off background loader
        self._loader = LoaderThread(file_path, self.bytes_per_line)
        self._loader.progress.connect(self.progress.setValue)
        self._loader.finished.connect(self._loader_done)
        self._loader.start()

    def _loader_done(self, hexdump: str, data: bytearray, ascii_tex: str) -> None:
        # populate UI
        self._raw = data
        self.view.setPlainText(hexdump)
        self.view.setReadOnly(False)
        self.ascii_text = ascii_tex

        # housekeeping UI
        self.progress.setVisible(False)
        self.status.setText(f"Loaded {len(self._raw):,} bytes from \u201C{os.path.basename(self._path)}\u201D")
        self._modified = False
        self.save_btn.setEnabled(False)

    # ------------------------------------------------------------------ Search / Jump
    def _do_search_or_jump(self) -> None:
        query = self.search_edit.text().strip()
        if not query:
            return
        if query.find("$") or query.find("0x"):
            # 1) Address jump syntax: $0300   0300   0x0300
            m = re.fullmatch(r"(?:0x|\$)?([0-9A-Fa-f]{1,8})", query)
            if m:
                addr = int(m.group(1), 16)
                if addr >= len(self._raw):
                    QMessageBox.warning(self, "Jump", f"Address 0x{addr:08X} exceeds file size.")
                else:
                    self._goto_offset(addr)
                return  # handled – done

        # 2) Hex / ASCII search -------------------------------------------
        hex_only = all(ch in "0123456789abcdefABCDEF " for ch in query)
        try:
            if hex_only and len(query.replace(" ", "")) % 2 == 0:
                pattern = bytes.fromhex(query.replace(" ", ""))
            else:
                pattern = query.encode()
        except ValueError:
            QMessageBox.warning(self, "Search", "Malformed hex input.")
            return

        idx = self._raw.find(pattern)
        if idx == -1:
            QMessageBox.information(self, "Search", "Pattern not found.")
            return

        self._goto_offset(idx)

    # ------------------------------------------------------------------ Navigation / status helpers
    def _goto_offset(self, line_offset: int, byte_offset : int | None = None) -> None:
        line = line_offset // self.bytes_per_line
        byte_in_line = (line_offset %  self.bytes_per_line)
        test = self._offset_to_byte(byte_in_line)
        cursor = self.view.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveMode.MoveAnchor, line)
        print(f"ByteOffset: {byte_offset}\nLineOffset: {line_offset}\nLine: {line}")
        cursor.movePosition(QTextCursor.Right,QTextCursor.MoveAnchor, test)
        self.view.setTextCursor(cursor)
        self.view.setFocus()
        self.status.setText(f"Offset: 0x{line_offset:08X} (line {line})")
        
        tcf = QTextCharFormat()
        tcf.setForeground(QtGui.QColor("red"))
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 2)

        selection = QtWidgets.QTextEdit.ExtraSelection()
        
        selection.cursor = cursor
        selection.format = tcf        
        self.view.setExtraSelections([selection])

    def _update_status_offset(self) -> None:
        off = self._offset_for_cursor(self.view.textCursor())
        if off is not None:
            self.status.setText(f"Offset: 0x{off:08X}")

    def _offset_for_cursor(self, cur: QtGui.QTextCursor) -> int | None:
        """Very lightweight char‑to‑offset mapping based on fixed‑width layout."""
        line_idx = cur.blockNumber()
        col = cur.positionInBlock()
        if col < 10:  # inside the address column
            return None
        byte_idx = (col - 10) // 3  # 'XX ' pattern → 3 chars per byte
        off = line_idx * self.bytes_per_line + byte_idx
        return off if off < len(self._raw) else None
    
    def _offset_to_byte(self, byte: int) -> int | None:
        if byte == 0:
            return 10
        base_offset = 10
        col_off = 0
        if (byte > 8):
            col_off = 1
        byte_offset = (base_offset + byte * 3) + col_off
        return byte_offset

    # ------------------------------------------------------------------ Save logic
    def _mark_modified(self) -> None:
        if not self.view.isReadOnly():
            self._modified = True
            self.save_btn.setEnabled(True)

    def _save_changes(self) -> None:
        if not self._modified or not self._path:
            return

        if (
            QMessageBox.question(
                self,
                "Save changes",
                f"Overwrite \u201C{os.path.basename(self._path)}\u201D with current edits?",
            )
            != QMessageBox.Yes
        ):
            return

        new_data = self._parse_hex_view(self.view.toPlainText())
        if new_data is None:
            QMessageBox.critical(self, "Save", "Unable to parse modified hex view – aborting.")
            return

        try:
            with open(self._path, "rb+") as fp:
                fp.write(new_data)
                fp.truncate()
        except OSError as err:
            QMessageBox.critical(self, "Save", f"Write failed: {err}")
            return

        self._raw = new_data
        self._modified = False
        self.save_btn.setEnabled(False)
        self.status.setText("Saved successfully.")

    # ------------------------------------------------------------------ Helpers
    def _parse_hex_view(self, text: str) -> bytearray | None:
        """Translate the edited dump back into raw bytes (see previous revision for details)."""
        out = bytearray()
        hex_byte = re.compile(r"^[0-9A-Fa-f]{2}$")

        try:
            for ln, line in enumerate(text.splitlines(), start=1):
                if ":" not in line:
                    continue
                body = line.split(":", 1)[1].lstrip()
                tokens: list[str] = []
                for tok in body.split():
                    if len(tokens) == self.bytes_per_line:
                        break
                    if hex_byte.fullmatch(tok):
                        tokens.append(tok)
                    else:
                        break
                if len(tokens) > self.bytes_per_line:
                    raise ValueError(
                        f"Line {ln}: too many hex bytes ({len(tokens)}). Expected <= {self.bytes_per_line}."
                    )
                out.extend(int(t, 16) for t in tokens)
            return out
        except Exception as err:
            print("parse error:", err, file=sys.stderr)
            return None
        
    def _on_lorom_btn(self, input: str):
        """ decide whether to convert a LoROM address or a bank number """
        # Match either a bank (2 hex digits) or full LoROM address (6 hex digits)
        # Allows optional '0x', '$' or no prefix
        bank_pattern = r'^(?:0x|\$)?([0-9A-Fa-f]{2})$'
        lorom_pattern = r'^(?:0x|\$)?([0-9A-Fa-f]{6})$'
        
        if re.match(bank_pattern, input):
            self.pc_addr = self._bank_start(input)
            self.lorom_text_box.setText(self.pc_addr)
            return
        elif re.match(lorom_pattern, input):
            self.pc_addr = self._lorom_to_pc(input)
            self.lorom_text_box.setText(self.pc_addr)
            return
        else:
            print("Invalid input format")
    
    def _lorom_to_pc(self, addr_hex: str, has_header: bool = False) -> str:
        """
        Convert a 24-bit LoROM address (e.g. '0x8486D0' or '8486D0')
        to a file offset.  Set has_header=True if the ROM still
        contains the 512-byte copier header.
        """
        addr = int(addr_hex, 16)

        pc = ((addr & 0x7F0000) >> 1) | (addr & 0x7FFF)
        if has_header:
            pc += 0x200
        return hex(pc)
    
    def _bank_start(self, bank_hex: str, has_header: bool = False) -> str:
        print(type(bank_hex))
        bank = int(bank_hex, 16) & 0x7F   # drop the high bit
        pc = bank * 0x8000
        pc_end = (pc + 32*1024) -1
        if has_header:
            pc += 0x200
        return "From: " + hex(pc) + " to: " + hex(pc_end)


# ---------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FileDump(sys.argv)
    w.resize(1000, 650)
    w.show()
    sys.exit(app.exec())
