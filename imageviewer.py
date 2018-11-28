# coding:utf-8
"""
A image viewer based on PySide shows images from openCV.

Python: ver 3.6.6. or above
Required Modules: PySide, numpy, openCV(3.2)
Author: Leo Cai
"""

from typing import List, Dict, Tuple, Set

import cv2
import numpy as np
from PySide.QtGui import *
from PySide.QtCore import Qt, QEvent, QPointF, QRectF

from ui_imageviewer import ImageViewerUI
from roi import RoiType, QGraphicsRoiItem

__version__ = "0.1"


class QImageViewer(ImageViewerUI):
    def __init__(self):
        super(QImageViewer, self).__init__()
        # data parameters
        self._image = np.array([])
        self._roi_color: Qt.GlobalColor = Qt.green
        self._rois: Set[QGraphicsRectItem] = set()
        self._duplicated_rois: Set[QGraphicsRectItem] = set()
        self._texts: Dict[str, QGraphicsTextItem] = {}

        # GUI parameters
        self._show_rois = False
        self._show_texts = False
        self._last_tool = ""
        self._current_tool = "Arrow"
        self.temporary_pan_flag = False
        self._panning = {"flag": False,
                         "x": 0,
                         "y": 0}
        self._drawing = {"flag": False,
                         "x": 0,
                         "y": 0}
        self._selecting = {"flag": False,
                           "x": 0,
                           "y": 0,
                           "rect": QGraphicsRectItem(0, 0, 0, 0)}

        # tool function dict
        self._tool_function = {"Arrow": self._arrow,
                               "Rect": lambda *args: self._draw_roi(RoiType.Rect, *args),
                               "Ellipse": lambda *args: self._draw_roi(RoiType.Ellipse, *args),
                               "Zoom": self.zoom,
                               "Fit": self.zoom_fit,
                               "Pan": self._pan}

        # checkable
        self._checkable_btns = {"Arrow": self.btn_arrow,
                                "Rect": self.btn_rect,
                                "Ellipse": self.btn_ellipse,
                                "Zoom": self.btn_zoom,
                                "Pan": self.btn_pan}

        # catch up events from view
        # self.view.viewport().installEventFilter(self)
        self.scene.installEventFilter(self)

        # connections
        self.btn_arrow.clicked.connect(lambda: self._check_button(self.btn_arrow))
        self.btn_rect.clicked.connect(lambda: self._check_button(self.btn_rect))
        self.btn_ellipse.clicked.connect(lambda: self._check_button(self.btn_ellipse))
        self.btn_zoom.clicked.connect(lambda: self._check_button(self.btn_zoom))
        self.btn_pan.clicked.connect(lambda: self._check_button(self.btn_pan))
        self.btn_zoom_fit.clicked.connect(self.zoom_fit)

    def resizeEvent(self, event):
        """
        Reset Image when window is resized.
        :param event:
        :return:
        """
        self.zoom_fit()
        self.refresh()
        event.accept()

    def changeEvent(self, event):
        """
        Reset Image when window is changed.
        :param event:
        :return:
        """
        self.zoom_fit()
        self.refresh()
        event.accept()

    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            if event.key() == Qt.Key_Space:
                # start temporary pan
                self.view.viewport().setCursor(Qt.OpenHandCursor)
                self._last_tool = self._current_tool
                self._current_tool = "Pan"
                self.btn_pan.setChecked(True)
                self.temporary_pan_flag = True
                self.setFocus()
                event.accept()

            elif event.key() == Qt.Key_Alt:
                if self._current_tool == "Zoom":
                    self.view.viewport().setCursor(self.zoom_out_cursor)

        else:
            event.ignore()

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            if event.key() == Qt.Key_Space:
                # stop temporary pan
                self._current_tool = self._last_tool
                self.btn_pan.setChecked(False)
                self.temporary_pan_flag = False

                try:
                    self._checkable_btns[self._current_tool].setChecked(True)
                    self._tool_function[self._current_tool](event, QApplication.keyboardModifiers())
                except KeyError:
                    pass    # in case of no last tool checked before temporary panning

                self.setFocus()
                event.accept()
            elif event.key() == Qt.Key_Alt:
                if self._current_tool == "Zoom":
                    self.view.viewport().setCursor(self.zoom_in_cursor)

            elif event.key() == Qt.Key_Delete:
                selected_rois = set()
                for i, item in enumerate(self._rois):
                    if item.isSelected():
                        selected_rois.add(item)
                self.remove_rois(selected_rois)
        else:
            event.ignore()

    def eventFilter(self, obj, event):
        super(QGraphicsScene, self.scene).eventFilter(obj, event)
        if obj is self.scene:
            modifiers = QApplication.keyboardModifiers()
            try:
                self._tool_function[self._current_tool](event, modifiers)
            except KeyError:
                pass
        return QWidget.eventFilter(self, obj, event)

    @staticmethod
    def is_overlap(rect1: QRectF, rect2: QRectF):
        if rect1.x() + rect1.width() > rect2.x() and\
                rect2.x() + rect2.width() > rect1.x() and\
                rect1.y() + rect1.height() > rect2.y() and\
                rect2.y() + rect2.height() > rect1.y():
            return True
        else:
            return False

    def _check_button(self, btn: QPushButton):
        """
        Check the given button, uncheck the others and set the current tool.
        :param btn:
        :return:
        """
        for tool_btn in self._checkable_btns.values():
            tool_btn.setChecked(False)
        self.setFocus()

        if self.temporary_pan_flag:
            self._last_tool = btn.objectName()
            self._checkable_btns[self._last_tool].setChecked(True)
            self.btn_pan.setChecked(True)
        else:
            self._last_tool = self._current_tool = btn.objectName()
            # rois a mutable only when arrow is activated.
            status = True if self._current_tool == "Arrow" else False
            for item in self._rois:
                item.set_mutable(status)

            if self._current_tool == "Rect" or self._current_tool == "Ellipse":
                cursor = Qt.CrossCursor
            elif self._current_tool == "Zoom":
                cursor = self.zoom_in_cursor
            elif self._current_tool == "Pan":
                cursor = Qt.OpenHandCursor
            else:
                cursor = Qt.ArrowCursor

            self.view.viewport().setCursor(cursor)

            btn.setChecked(True)

    def _arrow(self, *args):
        event = args[0]
        modifier = args[1]  # for duplication

        if event.type() == QEvent.GraphicsSceneMousePress:
            pos = event.scenePos()
            if modifier == Qt.ControlModifier:

                if not any([roi.isSelected() for roi in self._rois]):
                    for roi in self._rois:
                        if self.is_overlap(roi.sceneBoundingRect(), QRectF(pos.x(), pos.y(), 0, 0)):
                            roi.setSelected(True)
                            break

                self._duplicated_rois = self._duplicate_roi()
                for roi in self._rois:
                    roi.setSelected(False)
                    roi.set_show_handle(False)

                for roi in self._duplicated_rois:
                    roi.setSelected(True)
                    roi.set_show_handle(False)

            else:
                # to check if mouse pressed in an ROI
                is_in_roi = False
                for roi in self._rois:
                    is_in_roi = self.is_overlap(roi.sceneBoundingRect(), QRectF(pos.x(), pos.y(), 0, 0))
                    if is_in_roi:
                        break

                if not is_in_roi:
                    # trigger the selecting mode if not in roi
                    self._selecting["x"] = pos.x()
                    self._selecting["y"] = pos.y()
                    self._selecting["flag"] = True

                    # show selecting rectangle
                    self._selecting["rect"].setRect(pos.x(), pos.y(), 0, 0)
                    self._selecting["rect"].setFlag(QGraphicsItem.ItemIsSelectable, True)
                    self.scene.addItem(self._selecting["rect"])

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            if self._selecting["flag"]:
                # update selecting rectangle and rois when moving mouse
                end_point = event.scenePos()

                # update selecting rectangle
                x0 = min((self._selecting["x"], end_point.x()))
                y0 = min((self._selecting["y"], end_point.y()))
                width = abs(self._selecting["x"] - end_point.x())
                height = abs(self._selecting["y"] - end_point.y())
                self._selecting["rect"].setRect(x0, y0, width, height)
                self._selecting["rect"].setSelected(True)

                # update outlooking of the ROIs
                for roi in self._rois:
                    if self.is_overlap(roi.sceneBoundingRect(), self._selecting["rect"].rect()):
                        # overlapped means selected roi
                        roi.setSelected(True)
                        roi.set_show_handle(True)
                    else:
                        # not selected
                        roi.setSelected(False)
                        roi.set_show_handle(False)

                    # repaint roi
                    roi.update()

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            end_point = event.scenePos()
            if self._selecting["flag"]:
                # disable selecting mode.
                self.scene.removeItem(self._selecting["rect"])

                if self._selecting["x"] == end_point.x() and self._selecting["y"] == end_point.y():
                    # deselect all rois when click mouse in background
                    for roi in self._rois:
                        roi.setSelected(False)
                        roi.set_show_handle(False)
                        roi.update()

            self._selecting["flag"] = False
            self._rois = self._rois | self._duplicated_rois

            for roi in self._duplicated_rois:
                roi.setSelected(False)
                roi.set_show_handle(False)
            self._duplicated_rois = set()

    def _draw_roi(self, roi_type: RoiType, *args):
        event = args[0]
        # self.view.viewport().setCursor(Qt.CrossCursor)
        global drawing_roi

        if event.type() == QEvent.GraphicsSceneMousePress:
            pos = event.scenePos()
            drawing_roi = self.add_roi(roi_type, pos.x(), pos.y(), 0, 0)
            self._drawing["flag"] = True
            self._drawing["x"] = pos.x()
            self._drawing["y"] = pos.y()

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            if self._drawing["flag"]:
                pos = event.scenePos()
                x0 = self._drawing["x"] if pos.x() > self._drawing["x"] else pos.x()
                y0 = self._drawing["y"] if pos.y() > self._drawing["y"] else pos.y()
                width = abs(pos.x() - self._drawing["x"])
                height = abs(pos.y() - self._drawing["y"])

                drawing_roi.setRect(x0, y0, width, height)

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            self._drawing["flag"] = False

    def _duplicate_roi(self) -> Set[QGraphicsRoiItem]:
        """
        Duplicate selected ROIs to end_point.
        """
        result = set()
        for roi in self._rois:
            if roi.isSelected():
                roi_copy = QGraphicsRoiItem(roi.roi_type,
                                            roi.sceneBoundingRect().x(),
                                            roi.sceneBoundingRect().y(),
                                            roi.rect().width(),
                                            roi.rect().height())
                # roi_copy.moveBy(roi.scenePos().x(), roi.scenePos().y())
                self.scene.addItem(roi_copy)
                result.add(roi_copy)
        return result

    def _pan(self, *args):
        event = args[0]

        # self.view.viewport().setCursor(Qt.OpenHandCursor)

        if event.type() == QEvent.GraphicsSceneMousePress:
            pos = event.scenePos()
            self._panning["flag"] = True
            self._panning["x"] = pos.x()
            self._panning["y"] = pos.y()

        elif event.type() == QEvent.GraphicsSceneMouseMove:
            if self._panning["flag"]:
                pos = event.scenePos()
                dx = pos.x() - self._panning['x']
                dy = pos.y() - self._panning['y']
                self.pix_map_item.moveBy(dx, dy)
                self.text_group.moveBy(dx, dy)
                for item in self._rois:
                    item.moveBy(dx, dy)
                self._panning["x"] = pos.x()
                self._panning["y"] = pos.y()

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            self._panning["flag"] = False
            self._panning["x"] = 0
            self._panning["y"] = 0

    def zoom(self, *args):
        event = args[0]
        modifiers = args[1]

        cursor = self.zoom_out_cursor if modifiers == Qt.AltModifier else self.zoom_in_cursor
        self.view.viewport().setCursor(cursor)

        if event.type() == QEvent.GraphicsSceneMouseRelease:
            factor = 1 / 1.2 if modifiers == Qt.AltModifier else 1.2
            self.view.scale(factor, factor)
            pos = event.scenePos()
            self.view.centerOn(pos.x(), pos.y())

    def zoom_fit(self, *args):
        self.setFocus()
        self.view.resetMatrix()
        self.pix_map_item.setPos(0, 0)
        self.text_group.setPos(0, 0)

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
        self.text_group.addToGroup(item)
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

    # def scene_pos(self, event: QMouseEvent):
    #     """
    #     Map the mouse position to self.scene from QMouseEvent
    #     :param event: QMouseEvent
    #     :return: Mapped mouse position
    #     """
    #     pos = event.globalPos()
    #     pos = self.view.mapFromGlobal(pos)
    #     pos = self.view.mapToScene(pos)
    #     return pos

    def add_roi(self, roi_type: RoiType, x: int, y: int, width: int, height: int):
        roi = QGraphicsRoiItem(roi_type, x, y, width, height)
        roi.setPen(QPen(self._roi_color))
        roi.set_mutable(False)
        self.scene.addItem(roi)
        self._rois.add(roi)
        return roi

    def remove_roi(self, roi: QGraphicsRoiItem):
        self.scene.removeItem(roi)
        self._rois.remove(roi)

    def remove_rois(self, rois: Set[QGraphicsRoiItem]):
        for item in rois:
            self.scene.removeItem(item)
        self._rois = self._rois - rois

    def clear_roi(self):
        for item in self._rois:
            self.scene.removeItem(item)
        self._rois.clear()

