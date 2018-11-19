# coding:utf-8
"""
A image viewer based on PySide shows images from openCV.

Python: ver 3.6.6. or above
Required Modules: PySide, numpy, openCV(3.2)
Author: Leo Cai
"""

import sys
import time
from typing import List, Dict, Tuple

import cv2
import numpy as np
from PySide.QtGui import *
from PySide.QtCore import Qt


__version__ = "0.1"


class QImageViewer(QWidget):
    def __init__(self):
        super(QImageViewer, self).__init__()
        # parameters
        self._image = np.array([])
        self._rois: List[Roi] = []
        self._texts: Dict[str, QGraphicsTextItem] = {}
        self._show_rois = False
        self._show_texts = False
        self._scale_factor = 1

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

        # tool bar
        self.toolbar = QToolBar()
        self.v_box.addWidget(self.toolbar)
        self.btn_zoom_in = QPushButton("Zoom in")
        self.toolbar.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("Zoom out")
        self.toolbar.addWidget(self.btn_zoom_out)

        self.btn_zoom_fit = QPushButton("Zoom to fit")
        self.toolbar.addWidget(self.btn_zoom_fit)
        self.toolbar.addSeparator()

        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn_zoom_fit.clicked.connect(self.zoom_fit)

    def paintEvent(self, event):
        # refresh view when resize or change.
        self.refresh()

    def mousePressEvent(self, event):
        pos = event.globalPos()
        pos = self.view.mapFromGlobal(pos)
        pos = self.view.mapToScene(pos)

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

    def zoom_in(self):
        self.view.scale(1.1, 1.1)

    def zoom_out(self):
        factor = 1 / 1.1
        self.view.scale(factor, factor)

    def zoom_fit(self):
        self.view.resetMatrix()


class Roi(object):
    def __init__(self, x, y, width, height, shape='oval', name=''):
        super(Roi, self).__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape
        self.name = name
