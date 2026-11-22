"""Render the mock-up screenshots offscreen: python tools/mockup.py OUT_DIR"""
import os
import sys
from pathlib import Path

import json
import tempfile

# A tall virtual screen so menus don't wrap into columns (the default offscreen screen is small).
_cfg = Path(tempfile.gettempdir()) / "pr7z_offscreen.json"
_cfg.write_text(json.dumps({"screens": [{"name": "mock", "x": 0, "y": 0, "width": 2560, "height": 3200,
                                          "logicalDpi": 96, "logicalBaseDpi": 96, "dpr": 1}]}))
os.environ.setdefault("QT_QPA_PLATFORM", f"offscreen:configfile={_cfg}")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication

from pr7z import theme
from pr7z.add_dialog import AddDialog
from pr7z.main_window import MainWindow

out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
out.mkdir(parents=True, exist_ok=True)
app = QApplication([])
theme.load_fonts()
app.setPalette(theme.palette())
app.setStyleSheet(theme.stylesheet())

w = MainWindow()
w.show()
src = w.model.findItems("ELSEWORLD_master_24bit.wav")[0].index()
idx = w.proxy.mapFromSource(src)  # the view shows the sorted proxy, so select through it
w.view.selectionModel().select(idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
w.view.setCurrentIndex(idx)
app.processEvents()
w.grab().save(str(out / "main_window.png"))

menu = w.menuBar().actions()[0].menu()
menu.popup(w.mapToGlobal(w.menuBar().geometry().bottomLeft()))
app.processEvents()
menu.setActiveAction([a for a in menu.actions() if a.text().startswith("&Copy")][0])
app.processEvents()
menu.grab().save(str(out / "file_menu.png"))
menu.close()

d = AddDialog()
d.show()
app.processEvents()
d.grab().save(str(out / "add_dialog.png"))
print("ok")
