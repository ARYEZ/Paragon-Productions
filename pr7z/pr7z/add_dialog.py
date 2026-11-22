"""The "Add to Archive" dialog, with 7-Zip's fields, as Paragon dock panels."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout)

from .widgets import Header

FORMATS = ["7z", "tar", "wim", "zip", "gzip", "bzip2", "xz", "zstd"]
LEVELS = ["0 - Store", "1 - Fastest", "3 - Fast", "5 - Normal", "7 - Maximum", "9 - Ultra"]
METHODS = ["LZMA2", "LZMA", "PPMd", "BZip2"]
DICTS = ["64 KB", "1 MB", "4 MB", "16 MB", "32 MB", "64 MB", "128 MB", "256 MB", "512 MB", "1536 MB"]
WORDS = ["8", "16", "32", "64", "128", "256", "273"]
SOLID = ["Non-solid", "1 MB", "16 MB", "256 MB", "1 GB", "4 GB", "16 GB", "64 GB", "Solid"]
THREADS = [str(i) for i in range(1, 17)]
UPDATE_MODES = ["Add and replace files", "Update and add files", "Freshen existing files", "Synchronize files"]
PATH_MODES = ["Relative pathnames", "Full pathnames", "Absolute pathnames"]
VOLUMES = ["", "10M", "100M", "1000M", "650M - CD", "700M - CD", "4092M - FAT", "4480M - DVD"]


def _field(text: str) -> QLabel:
    lab = QLabel(text.upper())
    lab.setProperty("role", "field")
    return lab


def _combo(items, current=None, editable=False) -> QComboBox:
    c = QComboBox()
    c.addItems(items)
    c.setEditable(editable)
    if current is not None:
        c.setCurrentText(current)
    return c


class AddDialog(QDialog):
    def __init__(self, archive_path: str = r"D:\Music\ELSEWORLD_Stems.7z", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add to Archive")
        self.resize(900, 640)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 16)
        root.setSpacing(0)
        root.addWidget(Header("ADD TO ARCHIVE"))

        body = QVBoxLayout()
        body.setContentsMargins(20, 6, 20, 0)
        body.setSpacing(4)

        # Archive path
        arch = QGroupBox("ARCHIVE")
        al = QHBoxLayout(arch)
        self.archive = _combo([archive_path], editable=True)
        browse = QPushButton("...")
        browse.setFixedWidth(44)
        al.addWidget(self.archive, 1)
        al.addWidget(browse)
        body.addWidget(arch)

        cols = QHBoxLayout()
        cols.setSpacing(12)

        # Left: compression
        comp = QGroupBox("COMPRESSION")
        g = QGridLayout(comp)
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(7)
        rows = [
            ("Archive format", _combo(FORMATS, "7z")),
            ("Compression level", _combo(LEVELS, "5 - Normal")),
            ("Compression method", _combo(METHODS, "LZMA2")),
            ("Dictionary size", _combo(DICTS, "16 MB")),
            ("Word size", _combo(WORDS, "32")),
            ("Solid block size", _combo(SOLID, "16 GB")),
            ("CPU threads", _combo(THREADS, "8")),
        ]
        for r, (label, w) in enumerate(rows):
            g.addWidget(_field(label), r, 0)
            g.addWidget(w, r, 1)
        r = len(rows)
        mem = QLabel("Compressing  1 760 MB      Decompressing  18 MB")
        mem.setProperty("role", "dim")
        g.addWidget(_field("Memory usage"), r, 0)
        g.addWidget(mem, r, 1)
        g.addWidget(_field("Split to volumes, bytes"), r + 1, 0)
        g.addWidget(_combo(VOLUMES, "", editable=True), r + 1, 1)
        g.addWidget(_field("Parameters"), r + 2, 0)
        g.addWidget(QLineEdit(), r + 2, 1)
        g.setColumnStretch(1, 1)
        g.setRowStretch(r + 3, 1)
        cols.addWidget(comp, 1)

        # Right: update / options / encryption
        right = QVBoxLayout()
        right.setSpacing(4)
        upd = QGroupBox("UPDATE")
        ug = QGridLayout(upd)
        ug.setVerticalSpacing(7)
        ug.addWidget(_field("Update mode"), 0, 0)
        ug.addWidget(_combo(UPDATE_MODES), 0, 1)
        ug.addWidget(_field("Path mode"), 1, 0)
        ug.addWidget(_combo(PATH_MODES), 1, 1)
        ug.setColumnStretch(1, 1)
        right.addWidget(upd)

        opts = QGroupBox("OPTIONS")
        ol = QVBoxLayout(opts)
        ol.setSpacing(6)
        for text in ("Create SFX archive", "Compress shared files", "Delete files after compression"):
            ol.addWidget(QCheckBox(text))
        right.addWidget(opts)

        enc = QGroupBox("ENCRYPTION")
        eg = QGridLayout(enc)
        eg.setVerticalSpacing(7)
        pw1, pw2 = QLineEdit(), QLineEdit()
        for pw in (pw1, pw2):
            pw.setEchoMode(QLineEdit.Password)
        pw1.setText("elseworld")
        pw2.setText("elseworld")
        eg.addWidget(_field("Enter password"), 0, 0)
        eg.addWidget(pw1, 0, 1)
        eg.addWidget(_field("Reenter password"), 1, 0)
        eg.addWidget(pw2, 1, 1)
        eg.addWidget(QCheckBox("Show password"), 2, 1)
        eg.addWidget(_field("Encryption method"), 3, 0)
        eg.addWidget(_combo(["AES-256"]), 3, 1)
        encnames = QCheckBox("Encrypt file names")
        encnames.setChecked(True)
        eg.addWidget(encnames, 4, 1)
        eg.setColumnStretch(1, 1)
        right.addWidget(enc)
        right.addStretch(1)
        cols.addLayout(right, 1)
        body.addLayout(cols, 1)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 12, 0, 0)
        buttons.addStretch(1)
        ok = QPushButton("OK")
        ok.setDefault(True)
        for b in (ok, QPushButton("Cancel"), QPushButton("Help")):
            b.setMinimumWidth(96)
            buttons.addWidget(b)
        body.addLayout(buttons)
        root.addLayout(body, 1)
