import sys

import cv2
from PySide import QtGui

from imageviewer import QImageViewer, RoiType


app = QtGui.QApplication(sys.argv)
v = QImageViewer()
v.resize(1024, 680)
v.setWindowTitle("Image Viewer Example")
v.show()

img1 = cv2.imread("pictures/1.jpg")
v.set_image(img1)
v.add_text("txt1", "Text Example", color=(255, 255, 255), position=(0, 0))


v.add_roi_matrix(RoiType.Ellipse, rows=30, cols=40, dx=25, dy=15,
                 x=20, y=20, width=20, height=10)

v.save_rois("1.roi")


v.load_rois("1.roi")
sys.exit(app.exec_())
