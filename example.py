import sys

import cv2
from PySide import QtGui

from qimageviewer import QImageViewer


app = QtGui.QApplication(sys.argv)
v = QImageViewer()
v.setWindowTitle("Image Viewer Example")
v.show()
img1 = cv2.imread("pictures/1.jpg")
v.set_image(img1)
v.add_text("txt1", "Text Example", color=(255, 255, 255), position=(0, 0))
sys.exit(app.exec_())
