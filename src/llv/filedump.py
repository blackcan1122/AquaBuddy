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
from PySide6.QtGui import QFontDatabase, QTextCursor

from llv_utility import dump_line


class LoaderThread(QtCore.QThread):
    """Background loader that streams the file incrementally so the UI never blocks."""

    progress = QtCore.Signal(int)  # 0–100
    finished = QtCore.Signal(str, bytearray)  # hexdump string, raw bytes

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
                    line, _ = dump_line(addr, sub, self._bpl)
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

        self.finished.emit(hexdump, data)


class FileDump(QtWidgets.QWidget):
    """A simple hex‑viewer / editor widget with search & in‑place patching."""

    bytes_per_line = 16  # visual layout as well as search math

    def __init__(self, argv=None):
        super().__init__()
        self.setWindowTitle("FileDump – hex viewer / editor")

        # state ------------------------------------------------------------
        self._raw: bytearray = bytearray()
        self._path: str | None = None
        self._modified: bool = False

        # UI ---------------------------------------------------------------
        self._build_ui()

    # ------------------------------------------------------------------ UI helpers
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # file open / save --------------------------------------------------
        file_bar = QHBoxLayout()
        self.open_btn = QPushButton("Open…")
        self.save_btn = QPushButton("Save")
        self.save_btn.setEnabled(False)
        file_bar.addWidget(self.open_btn)
        file_bar.addWidget(self.save_btn)
        root.addLayout(file_bar)

        self.open_btn.clicked.connect(self._open_file)
        self.save_btn.clicked.connect(self._save_changes)

        # search ------------------------------------------------------------
        search_bar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search hex (e.g. DE AD BE EF) or ASCII text…")
        self.search_btn = QPushButton("Search")
        search_bar.addWidget(self.search_edit, 1)
        search_bar.addWidget(self.search_btn)
        root.addLayout(search_bar)

        self.search_btn.clicked.connect(self._do_search)

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

    def _loader_done(self, hexdump: str, data: bytearray) -> None:
        # populate UI
        self._raw = data
        self.view.setPlainText(hexdump)
        self.view.setReadOnly(False)

        # housekeeping UI
        self.progress.setVisible(False)
        self.status.setText(f"Loaded {len(self._raw):,} bytes from \u201C{os.path.basename(self._path)}\u201D")
        self._modified = False
        self.save_btn.setEnabled(False)

    # ------------------------------------------------------------------ Search
    def _do_search(self) -> None:
        query = self.search_edit.text().strip()
        if not query:
            return

        # detect & convert --------------------------------------------------
        hex_only = all(ch in "0123456789abcdefABCDEF " for ch in query)
        try:
            if hex_only and len(query.replace(" ", "")) % 2 == 0:
                pattern = bytes.fromhex(query.replace(" ", ""))
            else:
                pattern = query.encode()
        except ValueError:
            QMessageBox.warning(self, "Search", "Malformed hex input.")
            return

        # actual search -----------------------------------------------------
        idx = self._raw.find(pattern)
        if idx == -1:
            QMessageBox.information(self, "Search", "Pattern not found.")
            return

        self._goto_offset(idx)

    # ------------------------------------------------------------------ Navigation / status helpers
    def _goto_offset(self, offset: int) -> None:
        line = offset // self.bytes_per_line
        cursor = self.view.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line)
        self.view.setTextCursor(cursor)
        self.status.setText(f"Jumped to 0x{offset:08X}")

    def _update_status_offset(self) -> None:
        off = self._offset_for_cursor(self.view.textCursor())
        if off is not None:
            self.status.setText(f"Offset: 0x{off:08X}")

    def _offset_for_cursor(self, cur: QtGui.QTextCursor) -> int | None:
        """Very lightweight char‑to‑offset mapping based on fixed‑width layout."""
        line_idx = cur.blockNumber()
        col = cur.positionInBlock()
        if col < 10:  # within the address column
            return None
        rel = col - 10
        byte_idx = rel // 3  # 'XX ' pattern → 3 chars per byte (byte + space)
        off = line_idx * self.bytes_per_line + byte_idx
        return off if off < len(self._raw) else None

    # ------------------------------------------------------------------ Save logic
    def _mark_modified(self) -> None:
        """Flag document as dirty *only* for user edits (view must be writable)."""
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
        """Translate the edited dump back into raw bytes.

        Strategy
        --------
        * For each line, collect **up to** ``bytes_per_line`` two‑digit hex tokens
          immediately after the address column. The rest of the line (ASCII
          preview/comment) is ignored.
        * Abort and return ``None`` if a malformed token count would risk data
          corruption.
        """
        out = bytearray()
        hex_byte = re.compile(r"^[0-9A-Fa-f]{2}$")

        try:
            for ln, line in enumerate(text.splitlines(), start=1):
                if ":" not in line:
                    # likely blank or decorative line
                    continue

                # Drop the address part
                body = line.split(":", 1)[1].lstrip()

                tokens: list[str] = []
                for tok in body.split():
                    if len(tokens) == self.bytes_per_line:
                        break  # reached ASCII column
                    if hex_byte.fullmatch(tok):
                        tokens.append(tok)
                    else:
                        break  # first non‑hex marks ASCII column

                if len(tokens) > self.bytes_per_line:
                    raise ValueError(
                        f"Line {ln}: too many hex bytes ({len(tokens)}). Expected <= {self.bytes_per_line}."
                    )

                out.extend(int(t, 16) for t in tokens)
            return out
        except Exception as err:
            print("parse error:", err, file=sys.stderr)
            return None


# ---------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FileDump(sys.argv)
    w.resize(1000, 650)
    w.show()
    sys.exit(app.exec())
