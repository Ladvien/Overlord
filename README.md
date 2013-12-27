Overlord
========

The Overlord project is a feeble attempt to re-create a simple to use vision tracking software fo robots.

The concept is pretty simple:








[![ScreenShot](https://i1.ytimg.com/vi/WyMZ6iGWpj4/mqdefault.jpg)](https://www.youtube.com/watch?v=WyMZ6iGWpj4)

Details can be found here:

http://www.instructables.com/id/How-to-Track-your-Robot-with-OpenCV/

http://letsmakerobots.com/node/38208


Options:

  #Frames passed before object is considered tracked.
  overlord.trackingFidelityLim = 150
  
  #Frames to wait before moving.
  Defaults to 160
  overlord.waitedFrames = 160
  
  #How close to does the robot need to be? Greater is less accurate.
  Defaults to 5.
  overlord.targetProximity = 5
  
  #GUI X, Y 
  #Defaults to 0, 0
  overlord.guiX = 440
  overlord.guiY = 320
  
  #Random target constraint; so target doesn't get placed too far from center.
  #Defaults to 1, 640, 1, 480
  overlord.targetLeftLimit = 20
  overlord.targetRightLimit = 400
  overlord.targetBottomLimit = 320
  overlord.targetTopLimit = 20
