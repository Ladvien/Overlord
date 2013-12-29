#Overlord Module 1.1
#C. Thomas Brittain
#12/26/13

import cv2
import numpy as np
from math import atan2, degrees, pi 
import random
import math 

#Tests module
def printo():
    print "Overlord Module 1.3"
    print "C. Thomas Brittain"
    print "12/26/13"

#///////////////// Main Control Variables /////////////////////////////
def dVariables():
    #For converting the compass heading into an integer
    global intRx
    intRx = 0

    #Holds the frame index
    global iFrame
    iFrame = 0

    #How many frames before we consider the object being tracked.
    global trackingFidelityLim
    trackingFidelityLim = 150

    #How many frames to wait before moving.
    global waitedFrames
    waitedFrames = 160

    #Proximity to target threshold.
    global targetProximity
    targetProximity = 0

    #Target xLeft, xRight limits.
    global targetLeftLimit, targetRightLimit, targetTopLimit, targetBottomLimit
    targetLeftLimit = 1
    targetRightLimit = 640

    #Target yTop, yBottom
    targetTopLimit = 1
    targetBottomLimit = 480
    
    #Helps control the gui placement.
    global guiX
    global guiY
    guiX = 0
    guiY = 0
    
    #headingDegrees holds the compass heading. Lets make it an integer.
    global headingDegrees    
    headingDegrees = 0
    
    #Used to determine whether the first compass reading has arrived.
    global compassInitFlag
    compassInitFlag = False

    #Holds the compass raw heading at start.  This is used in adjCompass()
    global intialRawHeading
    intialRawHeading = 0    

    #///////////////// End Main Control Variables //////////////////////////

    #///////////////// Color Selector Variables //////////////////////////
    global selection, drag_start, tracking_state, show_backproj, down_x, down_y

    selection = None
    drag_start = None
    tracking_state = 0
    show_backproj = False

    down_x = 0
    down_y = 0    

    #///////////////// End Color Selector Variables ///////////////////////

    #///////////////// Serial Control Variables /////////////////////////////
    
    #Flag to assuring we have something to say serially.
    global tranx_ready
    global tranx
    tranx_ready = False
    #Carries what we have to say.
    tranx = ""

    #For getting information from the Arduino (tx was taken by Target X :P)
    global rx
    rx = " "

    #///////////////// End Serial Control Variables /////////////////////////



    #///////////////// Motor Control Variables /////////////////////////////

    #I've not used this yet, but I plan on scaling motor-firing duration based
    global right, left, forward, stop
    right = "2"
    left = "4"
    forward = "3"
    stop = "5"

    #how far away from the target
    global motorDuration
    motorDuration = 0

    #A flag variable for threading my motor timer.
    global motorBusy
    motorBusy = False

    #///////////////// End Motor Control Variables //////////////////////////

def onmouse(event, x, y, flags, param):
    global selection, drag_start, tracking_state, show_backproj, down_x, down_y
    x, y = np.int16([x, y]) #[sic] BUG
    if event == cv2.EVENT_LBUTTONDOWN:
        drag_start = (x, y)
        down_x = x
        down_y = y
        
        tracking_state = 0
    if event == cv2.EVENT_LBUTTONUP:
        #if flags & cv2.EVENT_FLAG_LBUTTON:
        #h, w = selcFrame.shape[:2]
        #print abs(x-down_x), abs(y-down_y)
        w, h = abs(x-down_x), abs(y-down_y)
        x0, y0 = drag_start
        x0, y0 = np.maximum(0, np.minimum([x0, y0], [x, y]))
        x1, y1 = np.minimum([w, h], np.maximum([x0, y0], [x, y]))
        selection = None
        print x1-x0, y1-y0
        if x1-x0 > 0 and y1-y0 > 0:
            selection = (x0, y0, x1, y1)
        else:
            drag_start = None
            if selection is not None:
                tracking_state = 1


def mapper(x, in_min, in_max, out_min, out_max):
    #This will map numbers onto others.
    return ((x-in_min)*(out_max -out_min)/(in_max - in_min) + out_min)

def compass(headingDegrees):
    global compassInitFlag
    global initialRawHeading
    global intRx

    #This sets the first compass reading to our 0*.
    if compassInitFlag == False:
       initialRawHeading = headingDegrees
       compassInitFlag = True
       print initialRawHeading
       exit 

    #This is the function that actually maps offsets the compass reading.
    global intialRawHeading
    if headingDegrees >= initialRawHeading:
        adjHeading = mapper(headingDegrees, initialRawHeading, 360, 0, (360-initialRawHeading))
    elif headingDegrees <= initialRawHeading:
        adjHeading = mapper(headingDegrees, 0, (initialRawHeading-1),(360-initialRawHeading), 360)
    
    #Here, our compass reading is loaded into intRx
    intRx = adjHeading

def otracker():
    #Create video capture
    cap = cv2.VideoCapture(0)

    best_cnt = 1    

    #Globalizing variables
    global rx
    global tranx
    global intRx
    global cxAvg  #<----I can't remember why...
    global iFrame 
    global shortestAngle
    global tranx_ready
    global targetBottomLimit, targetTopLimit, targetRightLimit, targetLeftLimit
    global trackingFidelityLim
    global left, right, forward
    global guiX, guiY

    global selection, drag_start, tracking_state, show_backproj
    global selcFrame

    #Variable to find target angle. (Used in turning the bot toward target.)
    shortestAngle = 0

    #Flag for getting a new target.
    newTarget = "Yes"
    
    #Dot counter. He's a hungry hippo...
    dots = 0
    
    #This holds the bot's centroid X & Y average
    cxAvg = 0
    cyAvg = 0

    #Stores old position for movement assessment.
    xOld = 0
    yOld = 0
    
    #Clearing the serial send string.
    printRx = " "
          
    while(1):
        
        #"printRx" is separate in case I want to parse out other sensor data
        #from the bot
        printRx = str(intRx)
        #Bot heading, unmodified
        headingDeg = printRx
        #Making it a number so we can play with it.
        intHeadingDeg = int(headingDeg)
        headingDeg = str(intHeadingDeg)
            
        #Strings to hold the "Target Lock" status.     
        stringXOk = " "
        stringYOk = " "
        
        #Incrementing frame index
        iFrame = iFrame + 1
            
        #Read the frames
        _,frame = cap.read()
    
        #Smooth it
        frame = cv2.blur(frame,(3,3))
        
        #frame for color selector.
        ret, selcFrame = cap.read()

        #Convert to hsv and find range of colors
        hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
        thresh = cv2.inRange(hsv,np.array((0, 105, 143)), np.array((32, 175, 213)))
        thresh2 = thresh.copy()
    
        #Find contours in the threshold image
        contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    
        #Finding contour with maximum area and store it as best_cnt
        max_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area:
                max_area = area
                best_cnt = cnt

        #Finding centroids of best_cnt and draw a circle there
        M = cv2.moments(best_cnt)
        cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
        cv2.circle(frame,(cx,cy),10,255,-1)
    
        #After X frames, it compares the bot's X and X average,
        #if they are the same + or - 5, it assumes the bot is being tracked.
        if iFrame >= trackingFidelityLim:
            if cxAvg < (cx + targetProximity) and cxAvg > (cx - targetProximity):
                xOld == cxAvg
                stringXOk = "X Lock"
            if cyAvg < (cy + targetProximity) and cyAvg > (cy - targetProximity):
                yOld == cyAvg
                stringYOk = "Y Lock"          
            
        #This is finding the average of the X cordinate.  Used for establishing
        #a visual link with the robot.
        #X
        cxAvg = cxAvg + cx
        cxAvg = cxAvg / 2
        #Y
        cyAvg = cyAvg + cy
        cyAvg = cyAvg / 2
        
        #//Finding the Target Angle/////////////////////////////////////
        
        #Target cordinates.
        #Randomizing target.
        if newTarget == "Yes":
            tX = random.randrange(targetLeftLimit, targetRightLimit, 1)
            tY = random.randrange(targetTopLimit, targetBottomLimit, 1)
            newTarget = "No"
        
        if iFrame >= 170:
            if tX > cxAvg -45 and tX < cxAvg + 45:
                print "Made it through the X"
                if tY > cyAvg -45 and tY < cyAvg + 45:
                    print "Made it through the Y"
                    newTarget = "Yes"
                    dots=dots+1
        
        #Slope
        dx = cxAvg - tX
        dy = cyAvg - tY
        
        #Quad I -- Good
        if tX >= cxAvg and tY <= cyAvg:
            rads = atan2(dy,dx)
            degs = degrees(rads)
            degs = degs - 90
        #Quad II -- Good
        elif tX >= cxAvg and tY >= cyAvg:
            rads = atan2(dx,dy)
            degs = degrees(rads)
            degs = (degs * -1)
        #Quad III
        elif tX <= cxAvg and tY >= cyAvg:
            rads = atan2(dx,-dy)
            degs = degrees(rads)
            degs = degs + 180
            #degs = 3
        elif tX <= cxAvg and tY <= cyAvg:
            rads = atan2(dx,-dy)
            degs = degrees(rads) + 180
            #degs = 4
        
        #Convert float to int
        targetDegs = int(math.floor(degs))
        
        #Variable to print the degrees offset from target angle.
        strTargetDegs = " "
        
        #Put the target angle into a string to printed.
        strTargetDegs = str(math.floor(degs))
               
        #///End Finding Target Angle////////////////////////////////////

        
        #//// Move Bot //////////////////////////////////////
        
        #targetDegs = Target angle
        #intHeadingDeg = Current Bot Angle
        
        #Don't start moving until things are ready.
        if iFrame >= waitedFrames:
            #This compares the bot's heading with the target angle.  It must
            #be +-30 for the bot to move forward, otherwise it will turn.
            shortestAngle = targetDegs - intHeadingDeg
            
            if shortestAngle > 180:
                shortestAngle -= 360
            
            if shortestAngle < -180:
                shortestAngle += 360
            
            if shortestAngle <= 30 and shortestAngle >= -31:
                #To work the Robvio NRF24L01 code the format is like so, T: tells it to transmit this date
                #S: tells it to print the data to the serial line after transmission, "1" is the message, and "\n"
                #specifies that it is complete.
                tranx = (forward)
                tranx_ready = True
                print forward + " = Forward"
                
            elif shortestAngle >= 1:
                tranx = (right)
                tranx_ready = True
                print right + " = Right"
                
            elif shortestAngle < 1:
                tranx = (left)
                tranx_ready = True
                print left + " = Left"
                
        
        #//// End Move Bot //////////////////////////////////
  
        
        #////////CV Dawing//////////////////////////////
        
        #Target circle
        cv2.circle(frame, (tX, tY), 10, (0, 0, 255), thickness=-1)
        
        #ser.write(botXY)
        
        #Background for text.
        cv2.rectangle(frame, (guiX+18,guiY+2), (guiX+170,guiY+160), (255,255,255), -1)

        #Target angle.
        cv2.line(frame, (tX,tY), (cxAvg,cyAvg),(0,255,0), 1)
        
        #Bot's X and Y is written to image
        cv2.putText(frame,str(cx)+" cx, "+str(cy)+" cy",(guiX+20,guiY+20),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
        
        #Bot's X and Y averages are written to image
        cv2.putText(frame,str(cxAvg)+" cxA, "+str(cyAvg)+" cyA",(guiX+20,guiY+40),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))

        #"Ok" is written to the screen if the X&Y are close to X&Y Avg for several iterations.
        cv2.putText(frame,stringXOk,(guiX+20,guiY+60),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
        cv2.putText(frame,stringYOk,(guiX+20,guiY+80),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))

        #Print the compass to the frame.
        cv2.putText(frame,"Bot: "+headingDeg+" Deg",(guiX+20,guiY+100),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
        cv2.putText(frame,"Target: "+strTargetDegs+" Deg",(guiX+20,guiY+120),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
        
        #Dots eaten.
        cv2.putText(frame,"Dots Ate: "+ str(dots),(guiX+20,guiY+140),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
                
        #After the frame has been modified to hell, show it.
        cv2.imshow('frame',frame) #Color image
        cv2.imshow('thresh',thresh2) #Black-n-White Threshold image

        cv2.setMouseCallback('frame', onmouse)
        
        #/// End CV Draw //////////////////////////////////////

        
        if cv2.waitKey(33)== 27:
            # Clean up everything before leaving
            cap.release()
            cv2.destroyAllWindows()
            #Tell the robot to stop before quit.
            ser.write("5") 
            ser.close() # Closes the serial connection.
            break
