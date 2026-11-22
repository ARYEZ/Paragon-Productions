"""Custom-painted Paragon widgets: the PR7-Z mark, the header, piano-black keys and line icons."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QRadialGradient, QRegion, QTransform)
from PySide6.QtWidgets import QAbstractButton, QHBoxLayout, QLabel, QWidget

from . import theme

# --------------------------------------------------------------------------- the PR7-Z mark
# Same construction as the PR7 plugins' Logo.cpp: letters designed 1 unit tall, upright,
# stems 0.24 wide, bars 0.2 tall, then slanted 0.3; two horizontal "speed cuts".
SLANT = 0.3
SPACING = 0.1
WIDTHS = [0.8, 0.84, 0.8, 0.4, 0.8]  # P, R, 7, dash, Z
TOTAL_WIDTH = sum(WIDTHS) + 4 * SPACING + SLANT
CUTS = [(0.63, 0.68), (0.79, 0.83)]


def _poly(path: QPainterPath, pts, x: float) -> None:
    path.moveTo(pts[0][0] + x, pts[0][1])
    for px, py in pts[1:]:
        path.lineTo(px + x, py)
    path.closeSubpath()


def _letters() -> tuple[QPainterPath, QPainterPath]:
    """(P, R, dash, Z) and the 7, in letter units with y down, slanted."""
    main, seven = QPainterPath(), QPainterPath()
    main.setFillRule(Qt.OddEvenFill)  # bowl counters are holes
    bowl = [(0, 0), (.64, 0), (.8, .15), (.8, .45), (.64, .6), (.24, .6), (.24, 1), (0, 1)]
    counter = [(.24, .2), (.56, .2), (.56, .4), (.24, .4)]
    x = 0.0
    _poly(main, bowl, x); _poly(main, counter, x)
    x += WIDTHS[0] + SPACING
    _poly(main, bowl, x); _poly(main, counter, x)
    _poly(main, [(.4, .6), (.64, .6), (.84, 1), (.6, 1)], x)  # R's leg
    x += WIDTHS[1] + SPACING
    _poly(seven, [(0, 0), (.8, 0), (.8, .2), (.44, 1), (.18, 1), (.5, .2), (0, .2)], x)
    x += WIDTHS[2] + SPACING
    _poly(main, [(0, .42), (.4, .42), (.4, .6), (0, .6)], x)  # dash, clear of the cuts
    x += WIDTHS[3] + SPACING
    # Z: 0.2 bars top and bottom, a 0.24-wide diagonal between them.
    _poly(main, [(0, 0), (.8, 0), (.8, .2), (.3, .8), (.8, .8), (.8, 1), (0, 1), (0, .8), (.5, .2), (0, .2)], x)
    # Lean forward: the top moves right, the baseline stays.
    lean = QTransform(1, 0, -SLANT, 1, SLANT, 0)  # x' = x + slant*(1 - y): y is down, so the top leans right
    return lean.map(main), lean.map(seven)


_MAIN, _SEVEN = _letters()


def draw_mark(p: QPainter, area: QRectF, glow: bool = True) -> QRectF:
    h = min(area.height(), area.width() / TOTAL_WIDTH)
    bounds = QRectF(area.x(), area.center().y() - h / 2, TOTAL_WIDTH * h, h)
    place = QTransform().translate(bounds.x(), bounds.y()).scale(h, h)
    main, seven = place.map(_MAIN), place.map(_SEVEN)
    sev_grad = theme.family_gradient(bounds.x(), 0, bounds.right(), 0)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    if glow:  # a soft neon halo behind the 7
        for ring in (3, 2, 1):
            c = QColor(theme.GLOW); c.setAlphaF(0.1 * (4 - ring))
            p.setPen(QPen(c, h * 0.07 * ring, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            p.drawPath(seven)
    clip = QRegion(bounds.adjusted(-h, -h, h, h).toAlignedRect())
    for top, bottom in CUTS:
        clip -= QRegion(QRectF(bounds.x() - h, bounds.y() + h * top, bounds.width() + 2 * h,
                               h * (bottom - top)).toAlignedRect())
    p.setClipRegion(clip)
    p.setPen(Qt.NoPen)
    p.fillPath(main, QColor(theme.TEXT))
    p.fillPath(seven, sev_grad)
    p.restore()
    return bounds


class Header(QWidget):
    """64 px family header: PARAGON and the PR7-Z mark, a panelEdge line under it."""

    def __init__(self, subtitle: str = "ARCHIVE MANAGER", parent=None):
        super().__init__(parent)
        self.subtitle = subtitle
        self.setFixedHeight(64)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.fillRect(r, QColor(theme.BACKGROUND))
        glow = QRadialGradient(QPointF(170, 0), 420)
        c = QColor(theme.GLOW); c.setAlphaF(0.07)
        glow.setColorAt(0, c); glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(r, glow)
        f = QFont("Inter", 1); f.setPixelSize(21)
        p.setFont(f); p.setPen(QColor(theme.TEXT))
        p.drawText(QRectF(22, 0, 200, r.height()), Qt.AlignVCenter | Qt.AlignLeft, "PARAGON")
        mark = draw_mark(p, QRectF(140, 19, 200, 26))
        f2 = QFont("Inter", 1); f2.setPixelSize(12); f2.setWeight(QFont.DemiBold)
        p.setFont(f2); p.setPen(QColor(theme.TEXT_DIM))
        p.drawText(QRectF(mark.right() + 16, 0, 300, r.height()), Qt.AlignVCenter | Qt.AlignLeft, self.subtitle)
        p.drawText(QRectF(0, 0, r.width() - 22, r.height()), Qt.AlignVCenter | Qt.AlignRight, "OBSIDIAN")
        p.setPen(QPen(QColor(theme.PANEL_EDGE), 1))
        p.drawLine(0, r.height() - 1, r.width(), r.height() - 1)


# --------------------------------------------------------------------------- line icons
def _icon_path(name: str) -> QPainterPath:
    """24x24 line drawings for the toolbar and file list."""
    p = QPainterPath()
    if name == "add":           # an archive box with a plus
        p.addRoundedRect(QRectF(3, 7, 18, 14), 2, 2); p.moveTo(3, 11); p.lineTo(21, 11)
        p.moveTo(12, 1); p.lineTo(12, 9); p.moveTo(8, 5); p.lineTo(16, 5)
    elif name == "extract":     # an arrow out of the box
        p.addRoundedRect(QRectF(3, 11, 18, 10), 2, 2)
        p.moveTo(12, 15); p.lineTo(12, 2); p.moveTo(7.5, 6.5); p.lineTo(12, 2); p.lineTo(16.5, 6.5)
    elif name == "test":        # a check in a circle
        p.addEllipse(QRectF(2.5, 2.5, 19, 19)); p.moveTo(7.5, 12.5); p.lineTo(10.5, 15.5); p.lineTo(16.5, 8.5)
    elif name == "copy":
        p.addRoundedRect(QRectF(8, 8, 13, 13), 2, 2)
        p.moveTo(16, 5); p.lineTo(16, 4); p.quadTo(16, 3, 15, 3); p.lineTo(4, 3); p.quadTo(3, 3, 3, 4)
        p.lineTo(3, 15); p.quadTo(3, 16, 4, 16); p.lineTo(5, 16)
    elif name == "move":
        p.moveTo(2, 12); p.lineTo(15, 12); p.moveTo(10.5, 7.5); p.lineTo(15, 12); p.lineTo(10.5, 16.5)
        p.moveTo(18, 4); p.lineTo(21, 4); p.lineTo(21, 20); p.lineTo(18, 20)
    elif name == "delete":
        p.moveTo(5, 5); p.lineTo(19, 19); p.moveTo(19, 5); p.lineTo(5, 19)
    elif name == "info":
        p.addEllipse(QRectF(2.5, 2.5, 19, 19)); p.moveTo(12, 11); p.lineTo(12, 17)
        p.addEllipse(QRectF(11, 6.5, 2, 2))
    elif name == "up":
        p.moveTo(12, 19); p.lineTo(12, 5); p.moveTo(6, 11); p.lineTo(12, 5); p.lineTo(18, 11)
    elif name == "folder":
        p.moveTo(2.5, 6); p.quadTo(2.5, 4.5, 4, 4.5); p.lineTo(9, 4.5); p.lineTo(11, 7); p.lineTo(20, 7)
        p.quadTo(21.5, 7, 21.5, 8.5); p.lineTo(21.5, 18); p.quadTo(21.5, 19.5, 20, 19.5); p.lineTo(4, 19.5)
        p.quadTo(2.5, 19.5, 2.5, 18); p.closeSubpath()
    elif name == "file":
        p.moveTo(5, 2.5); p.lineTo(14, 2.5); p.lineTo(19, 7.5); p.lineTo(19, 21.5); p.lineTo(5, 21.5)
        p.closeSubpath(); p.moveTo(14, 2.5); p.lineTo(14, 7.5); p.lineTo(19, 7.5)
    elif name == "archive":
        p.moveTo(5, 2.5); p.lineTo(19, 2.5); p.lineTo(19, 21.5); p.lineTo(5, 21.5); p.closeSubpath()
        for y in (4.5, 7.5, 10.5):
            p.moveTo(11, y); p.lineTo(13, y)
        for y in (6, 9):
            p.moveTo(13, y); p.lineTo(11, y)
        p.addRoundedRect(QRectF(10, 12, 4, 5), 1, 1)
    return p


def draw_icon(p: QPainter, name: str, rect: QRectF, colour: QColor | QLinearGradient, width: float = 1.8,
              fill: QColor | None = None) -> None:
    path = _icon_path(name)
    s = min(rect.width(), rect.height()) / 24.0
    t = QTransform().translate(rect.center().x() - 12 * s, rect.center().y() - 12 * s).scale(s, s)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    if fill is not None:
        p.fillPath(t.map(path), fill)
    pen = QPen(colour, width * s if s > 1.2 else width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.NoBrush)
    p.drawPath(t.map(path))
    p.restore()


def file_icon(kind: str, size: int = 18) -> QIcon:
    """Folder: orange line with a faint fill. File: pearl grey. Archive: family red."""
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    r = QRectF(0, 0, size, size)
    if kind == "folder":
        fill = QColor(theme.LED_ORANGE); fill.setAlphaF(0.16)
        draw_icon(p, "folder", r, QColor(theme.LED_ORANGE), 1.5, fill)
    elif kind == "archive":
        draw_icon(p, "archive", r, QColor(theme.ACCENT), 1.5)
    else:
        draw_icon(p, "file", r, QColor(theme.TEXT_DIM), 1.4)
    p.end()
    return QIcon(pm)


# --------------------------------------------------------------------------- piano-black keys
class KeyButton(QAbstractButton):
    """A toolbar key: the family's piano-black key (spec section 3) with an icon and an upper-case label."""

    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.icon_name, self.label = icon, label.upper()
        self.setFixedSize(QSize(78, 62))
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(label.title())

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        down = self.isDown()
        hover = self.underMouse() and self.isEnabled()
        r = QRectF(self.rect()).adjusted(3, 2, -3, -5)
        if down:
            r.translate(0, 1)
        # drop shadow
        sh = QColor(0, 0, 0, int(255 * (0.35 if down else 0.6)))
        p.setPen(Qt.NoPen); p.setBrush(sh)
        p.drawRoundedRect(r.translated(0, 2 if down else 3), 6, 6)
        # chamfer
        ch = QLinearGradient(r.topLeft(), r.bottomLeft())
        for pos, c in ((0, "#57565C"), (.18, "#2A292E"), (.7, "#111113"), (1, "#020203")):
            ch.setColorAt(pos, QColor(c))
        p.setBrush(ch); p.drawRoundedRect(r, 6, 6)
        # red glow in the side chamfers
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g0 = QColor(theme.GLOW); g0.setAlphaF(0); g1 = QColor(theme.GLOW); g1.setAlphaF(0.75)
        g.setColorAt(0, g0); g.setColorAt(1, g1)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(r.left(), r.top() + 4, 2.2, r.height() - 8), 1, 1)
        p.drawRoundedRect(QRectF(r.right() - 2.2, r.top() + 4, 2.2, r.height() - 8), 1, 1)
        # top face
        face = r.adjusted(3, 2.5, -3, -4)
        tf = QLinearGradient(face.topLeft(), face.bottomLeft())
        tf.setColorAt(0, QColor("#1C1B20")); tf.setColorAt(1, QColor("#060607"))
        p.setBrush(tf); p.drawRoundedRect(face, 4, 4)
        gloss = QColor(255, 255, 255, int(255 * 0.13))
        p.setBrush(gloss)
        p.save(); p.setClipRect(QRectF(face.left(), face.top(), face.width(), face.height() * 0.55))
        p.drawRoundedRect(face, 4, 4); p.restore()
        p.setPen(QPen(QColor(255, 255, 255, int(255 * 0.45)), 1))
        p.drawLine(QPointF(face.left() + 4, face.top() + 0.5), QPointF(face.right() - 4, face.top() + 0.5))
        p.setPen(QPen(QColor(0, 0, 0, int(255 * 0.6)), 0.8)); p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(face, 4, 4)
        outer = QColor(theme.GLOW) if hover else QColor("#000000")
        if hover:
            outer.setAlphaF(0.8)
        p.setPen(QPen(outer, 1)); p.drawRoundedRect(r.adjusted(-0.5, -0.5, 0.5, 0.5), 6.5, 6.5)
        # icon and label
        colour = QColor("#FFFFFF") if (hover or down) else QColor(theme.TEXT)
        if not self.isEnabled():
            colour = QColor(theme.TEXT_DIM)
        if not self.label:  # icon-only key (Up): centred
            side = min(18.0, face.height() - 6)
            draw_icon(p, self.icon_name, QRectF(face.center().x() - side / 2, face.center().y() - side / 2, side, side),
                      colour, 1.7)
            return
        draw_icon(p, self.icon_name, QRectF(face.center().x() - 11, face.top() + 7, 22, 22), colour, 1.7)
        f = QFont("Inter", 1); f.setPixelSize(10); f.setWeight(QFont.DemiBold)
        p.setFont(f); p.setPen(colour)
        p.drawText(QRectF(face.left(), face.bottom() - 19, face.width(), 15), Qt.AlignCenter, self.label)


class Toolbar(QWidget):
    """7-Zip's toolbar order: Add Extract Test | Copy Move Delete | Info."""

    triggered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 8)
        lay.setSpacing(6)
        groups = [[("add", "Add"), ("extract", "Extract"), ("test", "Test")],
                  [("copy", "Copy"), ("move", "Move"), ("delete", "Delete")],
                  [("info", "Info")]]
        self.keys: dict[str, KeyButton] = {}
        for i, group in enumerate(groups):
            if i:
                sep = QLabel(); sep.setFixedSize(1, 40)
                sep.setStyleSheet(f"background: {theme.PANEL_EDGE};")
                lay.addSpacing(8); lay.addWidget(sep); lay.addSpacing(8)
            for icon, label in group:
                k = KeyButton(icon, label)
                k.clicked.connect(lambda _=False, n=icon: self.triggered.emit(n))
                self.keys[icon] = k
                lay.addWidget(k)
        lay.addStretch(1)
