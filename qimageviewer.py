# coding:utf-8
"""
A image viewer based on PySide shows images from openCV.

Python: ver 3.6.6. or above
Required Modules: PySide, numpy, openCV(3.2)
Author: Leo Cai
"""

from typing import List, Dict, Tuple

import cv2
import numpy as np
from PySide.QtGui import *
from PySide.QtCore import Qt, QEvent


__version__ = "0.1"


class QImageViewer(QWidget):
    def __init__(self):
        super(QImageViewer, self).__init__()
        # data parameters
        self._image = np.array([])
        self._rois: List[Roi] = []
        self._texts: Dict[str, QGraphicsTextItem] = {}

        # GUI parameters
        self._show_rois = False
        self._show_texts = False
        # self._scale_factor = 1
        self._checkable_btns: Dict[str: QPushButton] = {}
        self._last_tool = ""
        self._current_tool = "Arrow"
        self._is_panning = False

        # layout
        self.v_box = QVBoxLayout()
        self.setLayout(self.v_box)

        # tool function dict
        self._tool_function = {"Arrow": self.arrow,
                               "Rect": self.draw_rect,
                               "Oval": self.draw_oval,
                               "Zoom": self.zoom,
                               "Fit": self.zoom_fit,
                               "Panning": self.panning}

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
        self.view.viewport().installEventFilter(self)

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
        self._checkable_btns["Arrow"] = self.btn_arrow

        self.btn_rect = QPushButton("Rect")
        self.btn_rect.setObjectName("Rect")
        self.btn_rect.setToolTip("Rect(R)")
        self.btn_rect.setShortcut("R")
        self.btn_rect.setCheckable(True)
        self.toolbar.addWidget(self.btn_rect)
        self._checkable_btns["Rect"] = self.btn_rect

        self.btn_oval = QPushButton("Oval")
        self.btn_oval.setObjectName("Oval")
        self.btn_oval.setToolTip("Oval(O)")
        self.btn_oval.setShortcut("O")
        self.btn_oval.setCheckable(True)
        self.toolbar.addWidget(self.btn_oval)
        self._checkable_btns["Oval"] = self.btn_oval

        self.toolbar.addSeparator()

        self.btn_zoom = QPushButton("Zoom")
        self.btn_zoom.setObjectName("Zoom")
        self.btn_zoom.setToolTip("Zoom(Z)")
        self.btn_zoom.setShortcut("Z")
        self.btn_zoom.setCheckable(True)
        self.toolbar.addWidget(self.btn_zoom)
        self._checkable_btns["Zoom"] = self.btn_zoom

        self.btn_zoom_fit = QPushButton("Fit")
        self.btn_zoom_fit.setObjectName("Fit")
        self.btn_zoom_fit.setToolTip("Fit(F)")
        self.btn_zoom_fit.setShortcut("F")
        self.toolbar.addWidget(self.btn_zoom_fit)

        self.toolbar.addSeparator()

        self.btn_panning = QPushButton("Panning")
        self.btn_panning.setObjectName("Panning")
        self.btn_panning.setToolTip("Panning(P/[Space])")
        self.btn_panning.setShortcut("P")
        self.btn_panning.setCheckable(True)
        self.toolbar.addWidget(self.btn_panning)
        self._checkable_btns["Panning"] = self.btn_panning

        # connections
        self.btn_arrow.clicked.connect(lambda: self.check_button(self.btn_arrow))
        self.btn_rect.clicked.connect(lambda: self.check_button(self.btn_rect))
        self.btn_oval.clicked.connect(lambda: self.check_button(self.btn_oval))
        self.btn_zoom.clicked.connect(lambda: self.check_button(self.btn_zoom))
        self.btn_panning.clicked.connect(lambda: self.check_button(self.btn_panning))
        self.btn_zoom_fit.clicked.connect(self.zoom_fit)

    @property
    def current_tool(self):
        return self._current_tool

    @current_tool.setter
    def current_tool(self, value: str):
        if value == "Arrow":
            self.view.unsetCursor()
        elif value == "Zoom":
            self.view.setCursor(self.zoom_in_cursor)
        self._current_tool = value

    def paintEvent(self, event):
        # refresh view when resize or change.
        self.refresh()

    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            if event.key() == Qt.Key_Space:
                # start temporary panning
                self._is_panning = True
                self._last_tool = self._current_tool
                self.current_tool = "Panning"
                self.btn_panning.setChecked(True)
                self.setFocus()
                event.accept()

            elif event.key() == Qt.Key_Control:
                if self.current_tool == "Zoom":
                    self.view.setCursor(self.zoom_out_cursor)

        else:
            event.ignore()

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            if event.key() == Qt.Key_Space:
                # stop temporary panning
                self.current_tool = self._last_tool
                self.btn_panning.setChecked(False)

                try:
                    self._checkable_btns[self._current_tool].setChecked(True)
                except KeyError:
                    pass    # in case of no last tool checked before space panning

                self.setFocus()
                self._is_panning = False
                event.accept()
            elif event.key() == Qt.Key_Control:
                if self.current_tool == "Zoom":
                    self.view.setCursor(self.zoom_in_cursor)
        else:
            event.ignore()

    def eventFilter(self, obj, event):
        if obj is self.view.viewport():
            modifiers = QApplication.keyboardModifiers()
            try:
                self._tool_function[self._current_tool](event, modifiers)
            except KeyError:
                pass
        return QWidget.eventFilter(self, obj, event)

    def refresh(self):
        if self._image.any():
            self.set_image(self._image)

    def get_image(self):
        # return the current image.
        return self._image

    def set_image(self, img: np.ndarray):
        if isinstance(img, np.ndarray):
            shape = img.shape
            if len(shape) == 2:
                # gray scale image
                self._image = img
                im = cv2.cvtColor(self._image, code=cv2.COLOR_GRAY2RGB)
            elif len(shape) == 3 and (shape[2] == 3):
                # color image
                self._image = img
                im = img
            else:
                raise TypeError("Image must be an openCV image(gray scale or BGR)!")
        else:
            raise TypeError("Image must be an openCV image(numpy ndarray)!")

        # cv2 image to QImage
        im_h, im_w, _ = im.shape
        bytes_per_line = im_w*3
        im = QImage(im.data, im_w, im_h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()   # bgr to rgb
        # QImage to QPixmap
        pix_map = QPixmap.fromImage(im)

        # scale
        view_w, view_h = self.view.width(), self.view.height()
        if im_h > view_h or im_w > view_w:
            # only auto scale when image is larger than view
            pix_map = pix_map.scaled(view_w, view_h, Qt.KeepAspectRatio)

        # update image in the view
        self.pix_map_item.setPixmap(pix_map)

        # keep the scene in the center of the view
        bounds = self.scene.itemsBoundingRect()
        self.view.setSceneRect(bounds)

    def add_text(self, name: str,
                 txt: str, *,
                 color: Tuple[int, int, int]=(0, 0, 0),
                 position: Tuple[int, int] = (0, 0)
                 ):
        item: QGraphicsTextItem = self.scene.addText(txt)
        item.setPos(position[0], position[1])
        item.setDefaultTextColor(QColor(color[0], color[1], color[2]))
        self._texts[name] = item

    def update_text(self, name: str, txt: str):
        self._texts[name].setPlainText(txt)

    def remove_text(self, name):
        self.scene.removeItem(self._texts[name])
        self._texts.pop(name)

    def show_toolbar(self, status: bool):
        if isinstance(status, bool):
            if status:
                self.toolbar.show()
            else:
                self.toolbar.hide()
        else:
            raise TypeError("Status must be bool!")

    def check_button(self, btn: QPushButton):
        """
        Check the given button, and uncheck the others
        :param btn:
        :return:
        """
        for tool_btn in self._checkable_btns.values():
            tool_btn.setChecked(False)
        self.setFocus()
        if not self._is_panning:
            self._last_tool = self.current_tool = btn.objectName()
            btn.setChecked(True)
        else:
            self._last_tool = btn.objectName()
            self.current_tool = self.btn_panning.objectName()
            self._checkable_btns[self._last_tool].setChecked(True)
            self.btn_panning.setChecked(True)

    def arrow(self, *args):
        pass

    def draw_rect(self, *args):
        pass

    def draw_oval(self, *args):
        pass

    def zoom(self, *args):
        event = args[0]
        modifiers = args[1]
        if event.type() == QEvent.MouseButtonRelease:
            factor = 1/1.2 if modifiers == Qt.ControlModifier else 1.2
            self.view.scale(factor, factor)

            pos = event.globalPos()
            pos = self.view.mapFromGlobal(pos)
            pos = self.view.mapToScene(pos)
            self.view.centerOn(pos.x(), pos.y())

    def zoom_fit(self, *args):
        self.setFocus()
        self.view.resetMatrix()

    def panning(self, *args):
        pass

    def coor(self, event):
        pos = event.globalPos()
        pos = self.view.mapFromGlobal(pos)
        self.view.centeron(pos.x(), pos.y())
        pos = self.view.mapToScene(pos)


class Roi(object):
    def __init__(self, x, y, width, height, shape='oval', name=''):
        super(Roi, self).__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape
        self.name = name
