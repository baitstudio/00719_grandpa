# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
# Created: Mon Jan 28 00:50:04 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(367, 464)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(Dialog)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":/res/tank_logo.png"))
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.groupBox = QtGui.QGroupBox(Dialog)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.template_preview = QtGui.QLabel(self.groupBox)
        self.template_preview.setObjectName("template_preview")
        self.gridLayout.addWidget(self.template_preview, 0, 2, 1, 1)
        self.label_8 = QtGui.QLabel(self.groupBox)
        self.label_8.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 7, 0, 1, 1)
        self.fields = QtGui.QLabel(self.groupBox)
        self.fields.setMinimumSize(QtCore.QSize(0, 60))
        self.fields.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.fields.setWordWrap(True)
        self.fields.setObjectName("fields")
        self.gridLayout.addWidget(self.fields, 7, 2, 1, 1)
        self.name = QtGui.QLineEdit(self.groupBox)
        self.name.setObjectName("name")
        self.gridLayout.addWidget(self.name, 3, 2, 1, 1)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.label_15 = QtGui.QLabel(self.groupBox)
        self.label_15.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_15.setObjectName("label_15")
        self.gridLayout.addWidget(self.label_15, 4, 0, 1, 1)
        self.context = QtGui.QLabel(self.groupBox)
        self.context.setMinimumSize(QtCore.QSize(0, 60))
        self.context.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.context.setWordWrap(True)
        self.context.setObjectName("context")
        self.gridLayout.addWidget(self.context, 4, 2, 1, 1)
        self.path = QtGui.QLabel(self.groupBox)
        self.path.setObjectName("path")
        self.gridLayout.addWidget(self.path, 8, 2, 1, 1)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 8, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem = QtGui.QSpacerItem(20, 26, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Hello Tank World!", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Template", None, QtGui.QApplication.UnicodeUTF8))
        self.template_preview.setText(QtGui.QApplication.translate("Dialog", "template", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("Dialog", "Fields", None, QtGui.QApplication.UnicodeUTF8))
        self.fields.setText(QtGui.QApplication.translate("Dialog", "<pre>{ foo: bar, \n"
"foor:bar }</pre>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Dialog", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.label_15.setText(QtGui.QApplication.translate("Dialog", "Context", None, QtGui.QApplication.UnicodeUTF8))
        self.context.setText(QtGui.QApplication.translate("Dialog", "<pre>{ foo: bar, \n"
"foor:bar }</pre>", None, QtGui.QApplication.UnicodeUTF8))
        self.path.setText(QtGui.QApplication.translate("Dialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Path", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
