from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, Qt
from PyQt5.QtWidgets import QDialog,QMessageBox
import cv2
import face_recognition
import numpy as np
import datetime
import os
import csv
import dlib
from imutils import face_utils
import webbrowser

import pymysql
import pandas.io.sql
import xlwt




class Ui_OutputDialog(QDialog):

    def __init__(self):
        super(Ui_OutputDialog, self).__init__()
        loadUi("./outputwindow.ui", self)

        #Update time
        now = QDate.currentDate()
        current_date = now.toString('ddd dd MMMM yyyy')
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.Date_Label.setText(current_date)
        self.Time_Label.setText(current_time)

        self.image = None

    @pyqtSlot()
    def startVideo(self, camera_name):
        """
        :param camera_name: link of camera or usb camera
        :return:
        """
        if len(camera_name) == 1:
        	self.capture = cv2.VideoCapture(int(camera_name))
        else:
        	self.capture = cv2.VideoCapture(camera_name)
        self.timer = QTimer(self)  # Create Timer
        path = 'ImagesAttendance'
        if not os.path.exists(path):
            os.mkdir(path)
        # known face encoding and known face name list
        images = []
        self.class_names = []
        self.encode_list = []
        self.TimeList1 = []
        self.TimeList2 = []
        self.time = 0
        self.lst = []
        attendance_list = os.listdir(path)

        # print(attendance_list)
        for cl in attendance_list:
            cur_img = cv2.imread(f'{path}/{cl}')
            images.append(cur_img)
            self.class_names.append(os.path.splitext(cl)[0])
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(img)
            encodes_cur_frame = face_recognition.face_encodings(img, boxes)[0]
            # encode = face_recognition.face_encodings(img)[0]
            self.encode_list.append(encodes_cur_frame)
        self.timer.timeout.connect(self.update_frame)  # Connect timeout to the output function
        self.timer.start(10)  # emit the timeout() signal at x=40ms

    def face_rec_(self, frame, encode_list_known, class_names):
        """
        :param frame: frame from camera
        :param encode_list_known: known face encoding
        :param class_names: known face names
        :return:
        """
        # csv

        def get_head_pose(shape):
            image_pts = np.float32([shape[17], shape[21], shape[22], shape[26], shape[36],
                                    shape[39], shape[42], shape[45], shape[31], shape[35],
                                    shape[48], shape[54], shape[57], shape[8]])

            _, rotation_vec, translation_vec = cv2.solvePnP(object_pts, image_pts, cam_matrix, dist_coeffs)

            reprojectdst, _ = cv2.projectPoints(reprojectsrc, rotation_vec, translation_vec, cam_matrix,
                                                dist_coeffs)

            reprojectdst = tuple(map(tuple, reprojectdst.reshape(8, 2)))

            # calc euler angle
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            pose_mat = cv2.hconcat((rotation_mat, translation_vec))
            _, _, _, _, _, _, euler_angle = cv2.decomposeProjectionMatrix(pose_mat)

            return reprojectdst, euler_angle

        def mark_attendance(name):
            """
            :param name: detected face known or unknown one
            :return:
            """

            if self.ClockInButton.isChecked():
                self.ClockInButton.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                        if (name != 'unknown'):
                            buttonReply = QMessageBox.question(self, 'Welcome ' + name, 'Ready to start test?' ,
                                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            if buttonReply == QMessageBox.Yes:

                                date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                                f.writelines(f'\n{name},{date_time_string},Clock In')
                                self.ClockInButton.setChecked(False)

                                self.NameLabel.setText(name)
                                self.StatusLabel.setText('Clocked In')
                                self.HoursLabel.setText('Measuring')
                                self.MinLabel.setText('')

                                # student getting most recent uploaded exam
                                db = pymysql.connect(
                                    host="localhost",
                                    user="root",
                                    passwd="",
                                    database="classroom"
                                )
                                cursor = db.cursor()

                                sql = "SELECT * FROM exams"
                                cursor.execute(sql)
                                a = cursor.fetchall()
                                examname = a[-1][2]
                                examlink = a[-1][3]
                                eid = a[-1][0]
                                print(examname, examlink, eid)
                                webbrowser.open_new(examlink)
                                #self.CalculateElapse(name)
                                #print('Yes clicked and detected')
                                self.Time1 = datetime.datetime.now()
                                #print(self.Time1)
                                self.ClockInButton.setEnabled(True)
                            else:
                                print('Not clicked.')
                                self.ClockInButton.setEnabled(True)
            elif self.ClockOutButton.isChecked():
                self.ClockOutButton.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                        if (name != 'unknown'):
                            buttonReply = QMessageBox.question(self, 'Cheers ' + name, 'Are you Clocking Out?',
                                                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            if buttonReply == QMessageBox.Yes:
                                date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                                f.writelines(f'\n{name},{date_time_string},Clock Out')
                                self.ClockOutButton.setChecked(False)

                                self.NameLabel.setText(name)
                                self.StatusLabel.setText('Clocked Out')
                                self.Time2 = datetime.datetime.now()


                                self.ElapseList(name)
                                self.TimeList2.append(datetime.datetime.now())
                                CheckInTime = self.TimeList1[-1]
                                CheckOutTime = self.TimeList2[-1]
                                self.ElapseHours = (CheckOutTime - CheckInTime)
                                self.MinLabel.setText("{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60)%60) + 'm')
                                self.HoursLabel.setText("{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60**2)) + 'h')
                                self.ClockOutButton.setEnabled(True)
                                #self.time = "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60)%60)
                                #average = (sum(lst) / len(lst))
                                print(average,float(((self.ElapseHours.total_seconds()))))

                                attention = (float((100 - average)*(len(self.lst))*2.5)) / float(((self.ElapseHours.total_seconds() )))
                                print(attention)
                                f.writelines(f'\ntotal duration {self.ElapseHours} ,total attention {attention}')
                                #__________________________________________________________________________
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
                                exam_id = 1
                                s = "INSERT INTO `performance`(`eid`, `uid`, `uattention`) VALUES (%s,%s,%s)"
                                val = (exam_id, uid, attention)
                                cursor.execute(s, val)
                                db.commit()
                                #___________________________________________________________________________
                            else:
                                print('Not clicked.')
                                self.ClockOutButton.setEnabled(True)

        # Head Pose

        face_landmark_path = './shape_predictor_68_face_landmarks.dat'

        K = [6.5308391993466671e+002, 0.0, 3.1950000000000000e+002,
             0.0, 6.5308391993466671e+002, 2.3950000000000000e+002,
             0.0, 0.0, 1.0]
        D = [7.0834633684407095e-002, 6.9140193737175351e-002, 0.0, 0.0, -1.3073460323689292e+000]

        cam_matrix = np.array(K).reshape(3, 3).astype(np.float32)
        dist_coeffs = np.array(D).reshape(5, 1).astype(np.float32)

        # 14 3D face model points
        object_pts = np.float32([[6.825897, 6.760612, 4.402142],
                                 [1.330353, 7.122144, 6.903745],
                                 [-1.330353, 7.122144, 6.903745],
                                 [-6.825897, 6.760612, 4.402142],
                                 [5.311432, 5.485328, 3.987654],
                                 [1.789930, 5.393625, 4.413414],
                                 [-1.789930, 5.393625, 4.413414],
                                 [-5.311432, 5.485328, 3.987654],
                                 [2.005628, 1.409845, 6.165652],
                                 [-2.005628, 1.409845, 6.165652],
                                 [2.774015, -2.080775, 5.048531],
                                 [-2.774015, -2.080775, 5.048531],
                                 [0.000000, -3.116408, 6.097667],
                                 [0.000000, -7.415691, 4.070434]])

        # 8 3D mapping points
        reprojectsrc = np.float32([[10.0, 10.0, 10.0],
                                   [10.0, 10.0, -10.0],
                                   [10.0, -10.0, -10.0],
                                   [10.0, -10.0, 10.0],
                                   [-10.0, 10.0, 10.0],
                                   [-10.0, 10.0, -10.0],
                                   [-10.0, -10.0, -10.0],
                                   [-10.0, -10.0, 10.0]])

        # Draw 12 3D volume coordinate points
        line_pairs = [[0, 1], [1, 2], [2, 3], [3, 0],
                      [4, 5], [5, 6], [6, 7], [7, 4],
                      [0, 7], [3, 4]]

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(face_landmark_path)
        face_rects = detector(frame, 0)
        shape = predictor(frame, face_rects[0])
        shape = face_utils.shape_to_np(shape)

        reprojectdst, euler_angle = get_head_pose(shape)
        for (x, y) in shape:
            cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

        for start, end in line_pairs:
            cv2.line(frame, reprojectdst[start], reprojectdst[end], (0, 0, 255))

        self.lst.append(float(format(euler_angle[2, 0])) + float(format(euler_angle[1, 0])) + float(format(euler_angle[0, 0])))
        average = abs(sum(self.lst) / len(self.lst))
        #print(len(self.lst),100-average)


        # face recognition
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)
        # count = 0
        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            match = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.50)
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "unknown"
            best_match_index = np.argmin(face_dis)
            # print("s",best_match_index)
            if match[best_match_index]:
                name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            mark_attendance(name)

        return frame

    def showdialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)


    def ElapseList(self,name):
        with open('Attendance.csv', "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 2

            Time1 = datetime.datetime.now()
            Time2 = datetime.datetime.now()
            for row in csv_reader:
                for field in row:
                    if field in row:
                        if field == 'Clock In':
                            if row[0] == name:
                                #print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time1 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList1.append(Time1)
                        if field == 'Clock Out':
                            if row[0] == name:
                                #print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time2 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList2.append(Time2)
                                #print(Time2)





    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.class_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):
        """
        :param image: frame from camera
        :param encode_list: known face encoding list
        :param class_names: known face names
        :param window: number of window
        :return:
        """
        image = cv2.resize(image, (640, 480))
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)
