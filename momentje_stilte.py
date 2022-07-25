# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 19:59:14 2022

@author: crnch
"""
from PyQt5 import QtCore, QtGui, QtWidgets
import sounddevice as sd
import numpy as np
import sys
import threading
from matplotlib.backends.backend_qt5agg import FigureCanvas
import matplotlib as mpl
import time

class MyFigureCanvas(FigureCanvas):
    '''
    This is the FigureCanvas in which the live plot is drawn.

    '''
    def __init__(self, x_len, y_range):
        '''
        :param x_len:       The nr of data points shown in one plot.
        :param y_range:     Range on y-axis.

        '''
        super().__init__(mpl.figure.Figure())
        # Range settings
        self._x_len_ = x_len
        self._y_range_ = y_range

        # Store two lists _x_ and _y_
        self._x_ = list(range(0, x_len))
        self._y_ = [0] * x_len

        # Store a figure ax
        self._ax_ = self.figure.subplots()
        
        self.xlineHeight = 0

        # Initiate the timer
        return

    def _update_canvas_(self, newY):
        '''
        This function gets called regularly by the timer.

        '''
        self._y_.append(newY)     # Add new datapoint
        self._y_ = self._y_[-self._x_len_:]                 # Truncate list _y_
        self._y_range_ = [0, max(self._y_[-self._x_len_:])]
        self._ax_.clear()                                   # Clear ax
        self._ax_.plot(self._x_, self._y_)                  # Plot y(x)
        self._ax_.set
        self._ax_.hlines(self.xlineHeight,
                         min(self._x_[-self._x_len_:]), 
                         max(self._x_len_, 
                             max(self._x_[-self._x_len_:])),
                         colors= 'red')
        self._ax_.set_ylim(ymin=self._y_range_[0], 
                           ymax=max(self._y_range_[1], self.xlineHeight+0.1))
        self.draw()
        return
    
    def setXlineHeight(self, h):
        self.xlineHeight = h


class mainWindow(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
    
        self.target = 10 #time in seconds
        self.threshold = 1 #arbitrary units
        
        self.initUI()
        self.setVolume()
        
        self.running = False
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTimer)
        self.listenThread = threading.Thread(target= self.listen,
                                              daemon = True)
    
    
    def initUI(self):
        
        self.setWindowTitle('Shhhhh')
        
        self.label = QtWidgets.QLabel('10.0')
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setFont(QtGui.QFont('Arial', 300))
        
        self.grid = QtWidgets.QGridLayout()
        self.timeDescrLabel = QtWidgets.QLabel("Hoe lang (seconden)")
        self.timeDescrLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.volDescrLabel = QtWidgets.QLabel("Hoe stil (lager is stiller)")
        self.volDescrLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.timeLabel = QtWidgets.QLabel(str(self.target))
        self.volLabel = QtWidgets.QLabel(str(self.threshold))
        self.timeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.timeSlider.setRange(10,30)
        self.timeSlider.valueChanged.connect(self.setTime)
        
        self.volSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)        
        self.volSlider.setRange(1,100)
        self.volSlider.valueChanged.connect(self.setVolume)
        
        hLay0 = QtWidgets.QHBoxLayout()
        hLay0.addWidget(self.timeDescrLabel)
        hLay0.addWidget(self.volDescrLabel)
        hLay1 = QtWidgets.QHBoxLayout()
        hLay1.addWidget(self.timeSlider)
        hLay1.addWidget(self.timeLabel)
        hLay1.addWidget(self.volSlider)
        hLay1.addWidget(self.volLabel)
        
        self.startStopBtn = QtWidgets.QPushButton("Start / stop")
        self.startStopBtn.pressed.connect(self.startStop)
        
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(hLay0)
        self.layout.addLayout(hLay1)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.startStopBtn)
        self.myFig = MyFigureCanvas(x_len=30, y_range=[0, 5])
        self.myFig.setXlineHeight(self.threshold)
        self.layout.addWidget(self.myFig)
        
        self.setLayout(self.layout)
        
        self.setGeometry(300, 100, 1000, 800)
        self.show()
        
        
    def updateTimer(self):
        if not self.running:
            return
        
        elapsed = self.t_start.elapsed()
        elapsed = self.target*1000 - elapsed
        sec_elapsed = int(elapsed/1000)
        ms_elapsed = int(elapsed%1000/100)
        text = str(sec_elapsed) + '.' + str(ms_elapsed)
        
        self.label.setText(text)
        
        if elapsed <= 0:
            self.running = False;
            self.label.setText("Klaar")
            
    def startStop(self):
        
        if not self.running:
            self.running = True
            self.t_start = QtCore.QTime.currentTime()
            self.timer.start(50)
            self.listenThread = threading.Thread(target= self.listen,
                                                  daemon = True)
            self.listenThread.start()
        
        else:
            self.running = False
            self.timer.stop()
            self.listenThread.join()
            
    def listen(self):

        while self.running:
            with sd.Stream(callback=self.print_sound):
                    sd.sleep(10000)
                    
    def setTime(self):
        self.target = self.timeSlider.value()
        self.t_start = QtCore.QTime.currentTime()
        self.timeLabel.setText(str(self.target))
        
    def setVolume(self):
        self.threshold = self.volSlider.value() / 20
        self.volLabel.setText(str(self.threshold))
        self.myFig.setXlineHeight(self.threshold)
            
    def print_sound(self, indata, outdata, frames, time, status):
        volume_norm = np.linalg.norm(indata)
        self.myFig._update_canvas_(volume_norm)
        if volume_norm > self.threshold:
            self.t_start = QtCore.QTime.currentTime()
        
        
    def closeEvent(self, event):
        #Turn off any threads that are still hanging
        
        self.listening = False
        time.sleep(0.1)
        
        if self.listenThread.is_alive():
            self.listenThread.join()
            
if __name__ == '__main__':
    
    app = QtWidgets.QApplication(sys.argv)
    ex = mainWindow()
    sys.exit(app.exec_())


#%%


