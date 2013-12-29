#Overlord Module 1.5
#C. Thomas Brittain
#12/26/13

import cv2
import numpy as np
from math import atan2, degrees, pi 
import random
import math 

#Tests module
def printo():
    print "Overlord Module 1.5"
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
    global mouseX, mouseY, trackBoxShow

    selection = None
    drag_start = None
    tracking_state = 0
    show_backproj = False

    trackBoxShow = False
    mouseX = 0
    mouseY = 0
    
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

#//////////////// WIP //////////////////////////////////
def onmouse(event, x, y, flags, param):
    global selection, drag_start, tracking_state, show_backproj, down_x, down_y, selcFrame
    global mouseX, mouseY, trackBoxShow
    x, y = np.int16([x, y]) #[sic] BUG
    mouseX = x
    mouseY = y
    if event == cv2.EVENT_LBUTTONDOWN:
        down_x = x
        down_y = y
        drag_start = (x, y)
        tracking_state = 0
        trackBoxShow = True
    if event == cv2.EVENT_LBUTTONUP:
        trackBoxShow = False
    if drag_start:
        if flags & cv2.EVENT_FLAG_LBUTTON:
            h, w = selcFrame.shape[:2]
            xo, yo = drag_start
            x0, y0 = np.maximum(0, np.minimum([xo, yo], [x, y]))
            x1, y1 = np.minimum([w, h], np.maximum([xo, yo], [x, y]))
            selection = None
            if x1-x0 > 0 and y1-y0 > 0:
                selection = (x0, y0, x1, y1)
        else:
            drag_start = None
            if selection is not None:
                tracking_state = 1
                

#//////////////// WIP //////////////////////////////////

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

    #These are the centroid of the camShift.
    global cscX
    global cscY
    cscX, cscY = 0, 0

    #Variable to find target angle. (Used in turning the bot toward target.)
    shortestAngle = 0

    #Flag for getting a new target.
    newTarget = True
    
    #Dot counter. He's a hungry hippo...
    dots = 0
    
    #Clearing the serial send string.
    printRx = " "
          
    while(1):
        #Read the frames
        _,frame = cap.read()
    
        #Smooth it
        frame = cv2.blur(frame,(3,3))

        #frame for color selector.
        ret, selcFrame = cap.read()
        vis = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
        
        #Code stolen from the camShift example.
        if selection:
            x0, y0, x1, y1 = selection
            track_window = (x0, y0, x1-x0, y1-y0)
            hsv_roi = hsv[y0:y1, x0:x1]
            mask_roi = mask[y0:y1, x0:x1]
            hist = cv2.calcHist( [hsv_roi], [0], mask_roi, [16], [0, 180] )
            cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX);
            hist = hist.reshape(-1)

        if tracking_state == 1:
            selection = None
            prob = cv2.calcBackProject([hsv], [0], hist, [0, 180], 1)
            prob &= mask
            term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
            track_box, track_window = cv2.CamShift(prob, track_window, term_crit)
            #Take the centroid of the CamShift.
            tupX, tupY = track_box[0][0], track_box[0][1]
            #Convert these numbers from floats in a tuple to an integer.
            cscX = int(tupX)
            cscY = int(tupY)
            if show_backproj:
                vis[:] = prob[..., np.newaxis]
        
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
            
        #Convert to hsv and find range of colors
        thresh = mask
        thresh2 = thresh.copy()

        #Randomizing target.
        if newTarget == True:
            tX = random.randrange(targetLeftLimit, targetRightLimit, 1)
            tY = random.randrange(targetTopLimit, targetBottomLimit, 1)
            newTarget = False

        #Did our robot eat the dot?
        if tX > cscX -45 and tX < cscX + 45:
            if tY > cscY -45 and tY < cscY + 45:
                newTarget = True
                dots=dots+1
        
        #Slope
        dx = cscX - tX
        dy = cscY - tY
        
        #Quad I -- Good
        if tX >= cscX and tY <= cscY:
            rads = atan2(dy,dx)
            degs = degrees(rads)
            degs = degs - 90
        #Quad II -- Good
        elif tX >= cscX and tY >= cscY:
            rads = atan2(dx,dy)
            degs = degrees(rads)
            degs = (degs * -1)
        #Quad III
        elif tX <= cscX and tY >= cscY:
            rads = atan2(dx,-dy)
            degs = degrees(rads)
            degs = degs + 180
        #Quad VI
        elif tX <= cscX and tY <= cscY:
            rads = atan2(dx,-dy)
            degs = degrees(rads) + 180
        
        #Convert float to int
        targetDegs = int(math.floor(degs))
        
        #Variable to print the degrees offset from target angle.
        strTargetDegs = " "
        
        #Put the target angle into a string to printed.
        strTargetDegs = str(math.floor(degs))
               
        #///End Finding Target Angle////////////////////////////////////

        
        #//// Move Bot //////////////////////////////////////
        
        #Don't start moving until things are ready.
        if iFrame >= waitedFrames:
            #This compares the bot's heading with the target angle.  It must
            #be +-30 for the bot to move forward, otherwise it will turn.
            shortestAngle = targetDegs - intHeadingDeg
            
            if shortestAngle > 180:
                shortestAngle -= 360
            if shortestAngle < -180:
                shortestAngle += 360
            #Do we move left, right, or forward.
            if shortestAngle <= 30 and shortestAngle >= -31:
                tranx = (forward)
                tranx_ready = True
            elif shortestAngle >= 1:
                tranx = (right)
                tranx_ready = True
            elif shortestAngle < 1:
                tranx = (left)
                tranx_ready = True
                
        
        #//// End Move Bot //////////////////////////////////
  
        
        #////////CV Dawing//////////////////////////////
        
        if tracking_state > 0:
            #Robot circle.
            cv2.circle(frame,(cscX,cscY),10,255,-1)
            print cscX, cscY
            #Target angle.
            cv2.line(frame, (tX,tY), (cscX, cscY),(0,255,0), 1)

        #Target circle
        cv2.circle(frame, (tX, tY), 10, (0, 0, 255), thickness=-1)
        
        #ser.write(botXY)
        
        #Background for text.
        cv2.rectangle(frame, (guiX+18,guiY+2), (guiX+170,guiY+160), (255,255,255), -1)
        
        if trackBoxShow == True:
            cv2.rectangle(frame, (down_x, down_y), (mouseX,mouseY), (0,255,0), 1)

        
        #Bot's X and Y is written to image
        cv2.putText(frame,str(cscX)+" cx, "+str(cscY)+" cy",(guiX+20,guiY+20),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))

        #Print the compass to the frame.
        cv2.putText(frame,"Bot: "+headingDeg+" Deg",(guiX+20,guiY+100),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
        cv2.putText(frame,"Target: "+strTargetDegs+" Deg",(guiX+20,guiY+120),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
        
        #Dots eaten.
        cv2.putText(frame,"Dots Ate: "+ str(dots),(guiX+20,guiY+140),cv2.FONT_HERSHEY_COMPLEX_SMALL,.7,(0,0,0))
                
        #After the frame has been modified to hell, show it.
        cv2.imshow('frame',frame) #Color image
        #cv2.imshow('thresh',thresh2) #Black-n-White Threshold image

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
