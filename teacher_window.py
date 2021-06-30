
from PyQt5.uic import loadUi

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog
import pymysql
import pandas.io.sql
import xlwt


class Ui_OutDialog(QDialog):

    def __init__(self):
        super(Ui_OutDialog, self).__init__()
        loadUi("./teacherwindow.ui", self)

        self.enterButton.clicked.connect(self.run)
        self.runDownload.clicked.connect(self.download)

    @pyqtSlot()
    def run(self):
        print("Clicked Run")


        db = pymysql.connect(
            host="localhost",
            user="root",
            passwd="",
            database="classroom"
        )
        cursor = db.cursor()



        sql = "SELECT * FROM temp"
        cursor.execute(sql)
        a = cursor.fetchone()
        uid = a[0]
        cursor.execute("DELETE FROM temp where uid = %d;" % uid)
        db.commit()
        print(uid)
        name = self.examName.text()  # input
        link = self.examLink.text()  # input

        sql = "INSERT INTO exams(uid,ename,elink) VALUES(%s, %s, %s)"
        print("here")
        val = (uid, name, link)
        cursor.execute(sql, val)
        db.commit()

    def download(self):
        db = pymysql.connect(
            host="localhost",
            user="root",
            passwd="",
            database="classroom"
        )
        cursor = db.cursor()

        # showing teacher -> performance result for particular exam
        # we will generate a csv file that will show results
        eid = 1  # teacher will select which exam results she wants to see
        cursor.execute("SELECT ename FROM exams where eid = %d;" % eid)
        a = cursor.fetchone()
        # print(a)
        # df = pandas.io.sql.read_sql("SELECT uid, uattention FROM performance WHERE eid = %d;" % eid , db)

        sq = "SELECT performance.uid, users.uname, performance.uattention FROM performance INNER JOIN users ON performance.uid=users.uid where performance.eid = 1"
        df = pandas.io.sql.read_sql(sq, db)
        file_name = 'report_for_' + a[0] + '.xls'
        df.to_excel(file_name)
        # it will create a .xls file where the program is saved




