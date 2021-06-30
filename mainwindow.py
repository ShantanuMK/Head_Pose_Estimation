import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog
#import MySQLdb as mdb
from out_window import Ui_OutputDialog
from teacher_window import Ui_OutDialog
import pymysql
import pandas.io.sql
import xlwt

class Ui_Dialog(QDialog):
    def __init__(self):
        super(Ui_Dialog, self).__init__()
        loadUi("mainwindow.ui", self)
        #self.radioStudent.toggled.connect(self.runSlot)

        self.runButton.clicked.connect(self.runSlot)

        self.lineEditPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self._new_window = None
        self.Videocapture_ = None

    def refreshAll(self):
        """
        Set the text of lineEdit once it's valid
        """
        self.Videocapture_ = "0"

    @pyqtSlot()
    def runSlot(self):
        """
        Called when the user presses the Run button
        """
        print("Clicked Run")
        self.labelResult.setText("You are logged in")
        self.refreshAll()
        print(self.Videocapture_)
        ui.hide()  # hide the main window

        db = pymysql.connect(
            host="localhost",
            user="root",
            passwd="",
            database="classroom"
        )

        cursor = db.cursor()

        login = self.lineEditUsername.text()  # input
        password = self.lineEditPassword.text()  # input

        sql = "SELECT * FROM users WHERE ulogin = %s and upassword = %s"

        values = (login, password)

        if cursor.execute(sql, values):
            #print("here")
            a = cursor.fetchone()
            uid = a[0]
            uname = a[1]
            udeg = a[-1]
            print(uid)
            print(uname)
            up = "INSERT INTO temp(uid) VALUES(%s)"
            val = (uid)
            cursor.execute(up, val)
            db.commit()
            if udeg == 0:
                self.outputWindow_()  # Create and open new output window
                print('Student')
            elif udeg == 1:
                self.outWindow_()
                # show teachers dashboard
                print('Teacher')

    def outputWindow_(self):
        """
        Created new window for visual output of the video in GUI
        """
        self._new_window = Ui_OutputDialog()
        self._new_window.show()
        self._new_window.startVideo(self.Videocapture_)
        print("Video Played")

    def outWindow_(self):
        """
        Created new window for visual output of the video in GUI
        """
        self._new_window = Ui_OutDialog()
        self._new_window.show()

        print("teacher's corner")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Ui_Dialog()
    ui.show()
    sys.exit(app.exec_())
