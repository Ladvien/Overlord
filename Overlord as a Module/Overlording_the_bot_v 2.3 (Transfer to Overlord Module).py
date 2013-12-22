import cv2
import numpy as np
import serial
from time import sleep
import threading
import math 
from math import atan2, degrees, pi 
import random
import overlord

#To test module.
overlord.printo()

#Open COM port to tether the bot.
ser = serial.Serial('COM19', 9600)

#For getting information from the Arduino (tx was taken by Target X :P)
global rx
rx = " "
#For sending information to the Arduino
global tranx
global tranx_ready 
#Flag to assuring we have something to say serially.
tranx_ready = "No"
#Carries what we have to say.
tranx = ""
#For converting the compass heading into an integer
global intRx
intRx = 0
#I've not used this yet, but I plan on scaling motor-firing duration based
#how far away from the target
global motorDuration
motorDuration = 0
#A flag variable for threading my motor timer.
global motorBusy
motorBusy = "No"
#Holds the frame index
global iFrame
iFrame = 0

#/////////////////// Overlord Module Settings //////////////////////

#Frames passed before object is considered tracked.
overlord.trackingFidelityLim = 150

#Frames to wait before moving.
overlord.waitedFrames = 160

#How close to does the robot need to be? Greater is less accurate.
overlord.targetProximity = 5

#GUI X, Y
overlord.guiX = 440
overlord.guiY = 320

#Random target constraint; so target doesn't get placed too far from center.
overlord.targetLeftLimit = 20
overlord.targetRightLimit = 400
overlord.targetBottomLimit = 320
overlord.targetTopLimit = 20

#/////////////////// Overlord Module Settings //////////////////////

def OpenCV():
    #Execute the Overlord.
    overlord.otracker()


def rx():
    #So the data can be passed to the OpenCV thread.
    global rx
    global intRx
    oldrx = 0
    while(True):
        # Read the newest output from the Arduino
        if ser.readline() != "":
            rx = ser.readline()
        
        #Delay one tenth of a second
        sleep(.1)
                
        #This is supposed to take only the first three digits.
        rx = rx[:3]
        
        #This removes any EOL characters
        rx = rx.strip()
        
        #If the number is less than 3 digits, then it will be included
        #we get rid of it so we can have a clean str to int conversion.
        rx = rx.replace(".", "")
        
        #We don't like 0.  So, this does away with it.        
        try:
            intRx = int(rx)
            oldrx = intRx
        except ValueError:
            intrx = oldrx


def motorTimer():
    global motorDuration
    global motorBusy
    global tranx_ready
    
    while(1):
        #This is for threading out the motor timer.  Allowing for control
        #over the motor burst duration.  There has to be both, something to write and
        #the motors can't be busy.
        if tranx_ready == "Yes" and motorBusy == "No":
            print "test2"
            ser.write(tranx)
            ser.flushOutput() #Clear the buffer?
            motorBusy = "Yes"
            tranx_ready = "No"
        if motorBusy == "Yes":
            sleep(.2) #Sets the motor burst duration.
            ser.write("T:S:5\n")
            sleep(.3) #Sets time inbetween motor bursts.
            motorBusy = "No"

#Threads OpenCV stuff.        
OpenCV = threading.Thread(target=OpenCV)
OpenCV.start()

#Threads the serial functions.
rx = threading.Thread(target=rx)
rx.start()

#Threads the motor functions.
motorTimer = threading.Thread(target=motorTimer)
motorTimer.start()

