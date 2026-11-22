"""The file-manager window, laid out like 7-Zip File Manager."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, QSortFilterProxyModel, Qt
from PySide6.QtGui import QAction, QColor, QPainter, QPen, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QMainWindow,
                               QStatusBar, QTreeView, QVBoxLayout, QWidget)

from . import theme
from .widgets import Header, KeyButton, Toolbar, file_icon

# 7-Zip's columns when browsing inside an archive.
ARCHIVE_COLUMNS = ["Name", "Size", "Packed Size", "Modified", "Attributes", "Encrypted", "CRC", "Method"]

MENUS = {
    "&File": ["&Open\tEnter", "Open &Inside\tCtrl+PgDown", "Open Out&side\tShift+Enter", "-", "&Edit\tF4",
              "Rena&me\tF2", "&Copy To...\tF5", "&Move To...\tF6", "&Delete\tDel", "-", "&Split file...",
              "Com&bine files...", "-", "P&roperties\tAlt+Enter", "Comme&nt...\tCtrl+Z", "Calculate checksum",
              "Diff", "-", "Create Folder\tF7", "Create File\tCtrl+N", "-", "E&xit\tAlt+F4"],
    "&Edit": ["Cu&t\tCtrl+X", "&Copy\tCtrl+C", "&Paste\tCtrl+V", "-", "Select &All\tShift+[Grey +]",
              "Deselect All\tShift+[Grey -]", "&Invert Selection\tGrey *", "Select...\tGrey +",
              "Deselect...\tGrey -", "Select by Type\tAlt+[Grey+]", "Deselect by Type\tAlt+[Grey -]"],
    "&View": ["Lar&ge Icons\tCtrl+1", "S&mall Icons\tCtrl+2", "&List\tCtrl+3", "&Details\tCtrl+4", "-",
              "Name\tCtrl+F3", "Type\tCtrl+F4", "Date\tCtrl+F5", "Size\tCtrl+F6", "Unsorted\tCtrl+F7", "-",
              "Flat View", "&2 Panels\tF9", "&Toolbars", "-", "Open Root Folder\t\\", "Up One Level\tBackspace",
              "Folders History...\tAlt+F12", "&Refresh\tCtrl+R", "Auto Refresh"],
    "F&avorites": ["&Add folder to Favorites as", "-", "Bookmark 1\tAlt+1", "Bookmark 2\tAlt+2"],
    "&Tools": ["&Options...", "&Benchmark"],
    "&Help": ["&Contents...\tF1", "-", "&About PR7-Z..."],
}

# Sample contents for the mock-up: browsing inside an archive.
SAMPLE = [
    ("folder", "Drums", "184 422 118", "121 905 774", "2026-11-18 21:04", "D", "-", "", ""),
    ("folder", "Guitars", "402 118 632", "290 412 006", "2026-11-18 21:06", "D", "-", "", ""),
    ("folder", "Vocals", "96 004 210", "71 220 880", "2026-11-19 09:12", "D", "-", "", ""),
    ("file", "ELSEWORLD_master_24bit.wav", "88 210 452", "61 004 118", "2026-11-19 22:41", "A", "+",
     "4F1A09C2", "LZMA2:26 7zAES"),
    ("file", "ELSEWORLD_session.cpr", "12 006 330", "3 220 914", "2026-11-19 22:43", "A", "+", "B2E07D15",
     "LZMA2:26 7zAES"),
    ("archive", "Alt_Mixes.zip", "54 118 090", "53 902 112", "2026-11-17 18:20", "A", "+", "90C4E3A1",
     "LZMA2:26 7zAES"),
    ("file", "cover_art_final.png", "18 772 004", "18 650 221", "2026-11-19 21:55", "A", "+", "1D7F44E8",
     "LZMA2:26 7zAES"),
    ("file", "lyrics.txt", "4 812", "1 930", "2026-11-12 14:02", "A", "+", "E5A0C3B7", "LZMA2:26 7zAES"),
    ("file", "notes_for_mix.md", "2 206", "1 004", "2026-11-18 23:30", "A", "+", "7C11F0D2", "LZMA2:26 7zAES"),
]


KIND_ROLE = Qt.UserRole + 1
SORT_ROLE = Qt.UserRole + 2


class FolderFirstProxy(QSortFilterProxyModel):
    """7-Zip's order: folders before files whichever way a column is sorted, names ignoring case."""

    def lessThan(self, left, right):
        lf = left.siblingAtColumn(0).data(KIND_ROLE) == "folder"
        rf = right.siblingAtColumn(0).data(KIND_ROLE) == "folder"
        if lf != rf:
            # Folders stay on top in both directions: invert for descending, since Qt flips the result.
            return lf if self.sortOrder() == Qt.AscendingOrder else rf
        a, b = left.data(SORT_ROLE), right.data(SORT_ROLE)
        if a is None or b is None:
            a, b = str(left.data() or "").casefold(), str(right.data() or "").casefold()
        return a < b


class FileView(QTreeView):
    """The list; a selected row gets one family-gradient band across its whole width (spec: @.22, gradient border)."""

    def drawRow(self, painter: QPainter, option, index):
        # Qt paints the row (including the alternating background) first; the band goes on top as a
        # translucent tint, otherwise the row background would cover it.
        super().drawRow(painter, option, index)
        if self.selectionModel().isRowSelected(index.row(), index.parent()):
            r = QRectF(option.rect)
            r.setLeft(0)
            r.setRight(self.viewport().width())
            painter.save()
            painter.fillRect(r, theme.family_gradient(r.left(), 0, r.right(), 0, theme.LIT, 0.22))
            painter.setPen(QPen(theme.family_gradient(r.left(), 0, r.right(), 0), 1))
            top, bottom = r.top() + 0.5, r.bottom() - 0.5
            painter.drawLine(QPointF(r.left(), top), QPointF(r.right(), top))
            painter.drawLine(QPointF(r.left(), bottom), QPointF(r.right(), bottom))
            painter.restore()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(r"D:\Music\ELSEWORLD_Stems.7z\ - Paragon PR7-Z")
        self.resize(1280, 760)
        self._build_menus()

        central = QWidget()
        col = QVBoxLayout(central)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(Header())
        self.toolbar = Toolbar()
        col.addWidget(self.toolbar)

        # Address bar: Up key and the editable path, as 7-Zip has it.
        addr = QHBoxLayout()
        addr.setContentsMargins(16, 4, 16, 8)
        addr.setSpacing(8)
        up = KeyButton("up", "")
        up.setFixedSize(QSize(40, 36))
        up.setToolTip("Up One Level (Backspace)")
        self.path = QComboBox()
        self.path.setEditable(True)
        self.path.addItems([r"D:\Music\ELSEWORLD_Stems.7z\\", r"D:\Music\\", "D:\\"])
        addr.addWidget(up)
        addr.addWidget(self.path, 1)
        col.addLayout(addr)

        # The list.
        self.view = FileView()
        self.view.setRootIsDecorated(False)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSortingEnabled(True)
        self.view.setUniformRowHeights(True)
        self.view.setIconSize(QSize(18, 18))
        self.model = QStandardItemModel(0, len(ARCHIVE_COLUMNS))
        self.model.setHorizontalHeaderLabels([c.upper() for c in ARCHIVE_COLUMNS])
        for kind, *cells in SAMPLE:
            row = [QStandardItem(c) for c in cells]
            row[0].setIcon(file_icon(kind))
            row[0].setData(kind, KIND_ROLE)
            row[0].setData(cells[0].casefold(), SORT_ROLE)
            for i in (1, 2):
                row[i].setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                row[i].setData(int(cells[i].replace(" ", "")), SORT_ROLE)  # sort sizes as numbers
            self.model.appendRow(row)
        self.proxy = FolderFirstProxy(self)
        self.proxy.setSourceModel(self.model)
        self.view.setModel(self.proxy)
        self.view.sortByColumn(0, Qt.AscendingOrder)
        hdr = self.view.header()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        for i, w in enumerate([300, 110, 110, 150, 90, 90, 100, 150]):
            hdr.resizeSection(i, w)
        hdr.setStretchLastSection(True)
        wrap = QHBoxLayout()
        wrap.setContentsMargins(16, 0, 16, 12)
        wrap.addWidget(self.view)
        col.addLayout(wrap, 1)
        self.setCentralWidget(central)

        # Status bar: 7-Zip's four fields.
        sb = QStatusBar()
        sb.setSizeGripEnabled(False)
        for text, stretch in (("1 object(s) selected", 0), ("88 210 452", 0), ("88 210 452", 0),
                              ("2026-11-19 22:41", 1)):
            lab = QLabel(text)
            sb.addWidget(lab, stretch)
        self.setStatusBar(sb)

    def _build_menus(self):
        bar = self.menuBar()
        for title, items in MENUS.items():
            menu = bar.addMenu(title)
            for item in items:
                if item == "-":
                    menu.addSeparator()
                else:
                    text, _, shortcut = item.partition("\t")
                    act = QAction(text, self)
                    if shortcut and "[" not in shortcut and "Grey" not in shortcut:
                        act.setShortcut(shortcut)
                    menu.addAction(act)
