"""
ROI item
"""

from enum import Enum, unique

from PySide.QtCore import Qt, QRectF, QPointF
from PySide.QtGui import QBrush, QPainterPath, QPainter, QPen
from PySide.QtGui import QGraphicsRectItem, QGraphicsItem


@unique
class RoiType(Enum):
    Rect = 0
    Ellipse = 1


class QGraphicsRoiItem(QGraphicsRectItem):
    handleTopLeft = 1
    handleTopMiddle = 2
    handleTopRight = 3
    handleMiddleLeft = 4
    handleMiddleRight = 5
    handleBottomLeft = 6
    handleBottomMiddle = 7
    handleBottomRight = 8

    handleSize = 0
    handleSpace = 4

    handleCursors = {
        handleTopLeft: Qt.SizeFDiagCursor,
        handleTopMiddle: Qt.SizeVerCursor,
        handleTopRight: Qt.SizeBDiagCursor,
        handleMiddleLeft: Qt.SizeHorCursor,
        handleMiddleRight: Qt.SizeHorCursor,
        handleBottomLeft: Qt.SizeBDiagCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
        handleBottomRight: Qt.SizeFDiagCursor,
    }

    def __init__(self, roi_type: RoiType, *args):
        """
        Initialize the shape.
        """
        super(QGraphicsRoiItem, self).__init__(*args)
        self.roi_type = roi_type
        self.color = Qt.green
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.set_mutable(True)
        self.update_handles_pos()

    def focusOutEvent(self, *args, **kwargs):
        self.handleSize = 0
        self.handleSpace = 4
        self.update_handles_pos()
        self.unsetCursor()

    def focusInEvent(self, *args, **kwargs):
        self.handleSize = +8.0
        self.handleSpace = -4.0
        self.update_handles_pos()

    def handle_at(self, point):
        """
        Returns the resize handle below the given point.
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def hoverMoveEvent(self, move_event):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """
        if self.isSelected():
            handle = self.handle_at(move_event.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(move_event)

    def hoverLeaveEvent(self, move_event):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(move_event)

    def mousePressEvent(self, mouse_event):
        """
        Executed when the mouse is pressed on the item.
        """
        self.handleSelected = self.handle_at(mouse_event.pos())
        if self.handleSelected:
            self.mousePressPos = mouse_event.pos()
            self.mousePressRect = self.boundingRect()
        super(QGraphicsRoiItem, self).mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event):
        """
        Executed when the mouse is being moved over the item while being pressed.
        """
        if self.handleSelected is not None:
            self.interactive_resize(mouse_event.pos())
        else:
            super().mouseMoveEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event):
        """
        Executed when the mouse is released from the item.
        """
        super().mouseReleaseEvent(mouse_event)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()

    def boundingRect(self):
        """
        Returns the bounding rect of the shape (including the resize handles).
        """
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def update_handles_pos(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft] = QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle] = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight] = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QRectF(b.right() - s, b.bottom() - s, s, s)

    def interactive_resize(self, mouse_pos):
        """
        Perform shape interactive resize.
        """
        offset = self.handleSize + self.handleSpace
        bounding_rect = self.boundingRect()
        rect = self.rect()
        diff = QPointF(0, 0)

        self.prepareGeometryChange()

        if self.handleSelected == self.handleTopLeft:

            from_x = self.mousePressRect.left()
            from_y = self.mousePressRect.top()
            to_x = from_x + mouse_pos.x() - self.mousePressPos.x()
            to_y = from_y + mouse_pos.y() - self.mousePressPos.y()
            diff.setX(to_x - from_x)
            diff.setY(to_y - from_y)
            bounding_rect.setLeft(to_x)
            bounding_rect.setTop(to_y)
            rect.setLeft(bounding_rect.left() + offset)
            rect.setTop(bounding_rect.top() + offset)

        elif self.handleSelected == self.handleTopMiddle:

            from_y = self.mousePressRect.top()
            to_y = from_y + mouse_pos.y() - self.mousePressPos.y()
            diff.setY(to_y - from_y)
            bounding_rect.setTop(to_y)
            rect.setTop(bounding_rect.top() + offset)

        elif self.handleSelected == self.handleTopRight:

            from_x = self.mousePressRect.right()
            from_y = self.mousePressRect.top()
            to_x = from_x + mouse_pos.x() - self.mousePressPos.x()
            to_y = from_y + mouse_pos.y() - self.mousePressPos.y()
            diff.setX(to_x - from_x)
            diff.setY(to_y - from_y)
            bounding_rect.setRight(to_x)
            bounding_rect.setTop(to_y)
            rect.setRight(bounding_rect.right() - offset)
            rect.setTop(bounding_rect.top() + offset)

        elif self.handleSelected == self.handleMiddleLeft:

            from_x = self.mousePressRect.left()
            to_x = from_x + mouse_pos.x() - self.mousePressPos.x()
            diff.setX(to_x - from_x)
            bounding_rect.setLeft(to_x)
            rect.setLeft(bounding_rect.left() + offset)

        elif self.handleSelected == self.handleMiddleRight:
            print("MR")
            from_x = self.mousePressRect.right()
            to_x = from_x + mouse_pos.x() - self.mousePressPos.x()
            diff.setX(to_x - from_x)
            bounding_rect.setRight(to_x)
            rect.setRight(bounding_rect.right() - offset)

        elif self.handleSelected == self.handleBottomLeft:

            from_x = self.mousePressRect.left()
            from_y = self.mousePressRect.bottom()
            to_x = from_x + mouse_pos.x() - self.mousePressPos.x()
            to_y = from_y + mouse_pos.y() - self.mousePressPos.y()
            diff.setX(to_x - from_x)
            diff.setY(to_y - from_y)
            bounding_rect.setLeft(to_x)
            bounding_rect.setBottom(to_y)
            rect.setLeft(bounding_rect.left() + offset)
            rect.setBottom(bounding_rect.bottom() - offset)

        elif self.handleSelected == self.handleBottomMiddle:

            from_y = self.mousePressRect.bottom()
            to_y = from_y + mouse_pos.y() - self.mousePressPos.y()
            diff.setY(to_y - from_y)
            bounding_rect.setBottom(to_y)
            rect.setBottom(bounding_rect.bottom() - offset)

        elif self.handleSelected == self.handleBottomRight:

            from_x = self.mousePressRect.right()
            from_y = self.mousePressRect.bottom()
            to_x = from_x + mouse_pos.x() - self.mousePressPos.x()
            to_y = from_y + mouse_pos.y() - self.mousePressPos.y()
            diff.setX(to_x - from_x)
            diff.setY(to_y - from_y)
            bounding_rect.setRight(to_x)
            bounding_rect.setBottom(to_y)
            rect.setRight(bounding_rect.right() - offset)
            rect.setBottom(bounding_rect.bottom() - offset)

        # handle the case of width or height < 0
        width = abs(rect.width())
        height = abs(rect.height())
        x0 = rect.x() if rect.width() > 0 else rect.x() - width
        y0 = rect.y() if rect.height() > 0 else rect.y() - height

        self.setRect(x0, y0, width, height)
        self.update_handles_pos()

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        """
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        """
        # painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        painter.setPen(QPen(self.color, 1.0, Qt.SolidLine))
        if self.roi_type == RoiType.Rect:
            painter.drawRect(self.rect())
        else:
            painter.drawEllipse(self.rect())

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(self.color, 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for handle, rect in self.handles.items():
            if self.handleSelected is None or handle == self.handleSelected:
                painter.drawEllipse(rect)

    def set_mutable(self, status: bool):
        """
        set the item mutable or immutable.
        :param status:
        :return:
        """
        self.setAcceptHoverEvents(status)
        self.setAcceptedMouseButtons(status)
        self.setFlag(QGraphicsItem.ItemIsMovable, status)
        self.setFlag(QGraphicsItem.ItemIsSelectable, status)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, status)
        self.setFlag(QGraphicsItem.ItemIsFocusable, status)

