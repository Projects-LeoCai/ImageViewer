from PySide.QtGui import *
from PySide.QtCore import Qt


class ImageViewerUI(QWidget):
    def __init__(self):
        super(ImageViewerUI, self).__init__()
        # layout
        self.v_box = QVBoxLayout()
        self.setLayout(self.v_box)

        # image view
        self.pix_map_item = QGraphicsPixmapItem()
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 0, 0)
        self.scene.addItem(self.pix_map_item)

        self.view = QGraphicsView(self.scene)
        self.v_box.addWidget(self.view)
        self.view.setMinimumSize(400, 300)
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # cursors
        self.zoom_in_cursor = QCursor(QPixmap(r"pictures\zi.png"))
        self.zoom_out_cursor = QCursor(QPixmap(r"pictures\zo.png"))

        # tool bar
        self.toolbar = QToolBar()
        self.v_box.addWidget(self.toolbar)

        self.btn_arrow = QPushButton("Arrow")
        self.btn_arrow.setObjectName("Arrow")
        self.btn_arrow.setToolTip("Arrow(A)")
        self.btn_arrow.setShortcut("A")
        self.btn_arrow.setCheckable(True)
        self.btn_arrow.setChecked(True)
        self.toolbar.addWidget(self.btn_arrow)

        self.toolbar.addSeparator()

        self.btn_rect = QPushButton("Rect")
        self.btn_rect.setObjectName("Rect")
        self.btn_rect.setToolTip("Rect(R)")
        self.btn_rect.setShortcut("R")
        self.btn_rect.setCheckable(True)
        self.toolbar.addWidget(self.btn_rect)

        self.btn_oval = QPushButton("Oval")
        self.btn_oval.setObjectName("Oval")
        self.btn_oval.setToolTip("Oval(O)")
        self.btn_oval.setShortcut("O")
        self.btn_oval.setCheckable(True)
        self.toolbar.addWidget(self.btn_oval)

        self.toolbar.addSeparator()

        self.btn_zoom = QPushButton("Zoom")
        self.btn_zoom.setObjectName("Zoom")
        self.btn_zoom.setToolTip("Zoom(Z)")
        self.btn_zoom.setShortcut("Z")
        self.btn_zoom.setCheckable(True)
        self.toolbar.addWidget(self.btn_zoom)

        self.btn_zoom_fit = QPushButton("Fit")
        self.btn_zoom_fit.setObjectName("Fit")
        self.btn_zoom_fit.setToolTip("Fit(F)")
        self.btn_zoom_fit.setShortcut("F")
        self.toolbar.addWidget(self.btn_zoom_fit)

        self.toolbar.addSeparator()

        self.btn_pan = QPushButton("Pan")
        self.btn_pan.setObjectName("Pan")
        self.btn_pan.setToolTip("Pan(P/[Space])")
        self.btn_pan.setShortcut("P")
        self.btn_pan.setCheckable(True)
        self.toolbar.addWidget(self.btn_pan)
