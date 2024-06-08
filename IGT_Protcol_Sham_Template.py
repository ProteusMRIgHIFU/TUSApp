
import sys
import os
# Change to correct path
sys.path.append('C:\\Users\\HIFUPC\\Documents\\IGTFUS-SDK-1.8.0\\python\\Python39x64')
import FUSTHON
import utils
import H317Functions
import time
import transducerXYZ
import random
import sounddevice as sd


###PART1
# User Defined Parameters
frequencyUS = 7e5 # in Hz
PRF = 500 # in Hz
dutyCycle = 30 # in %
totalUSDuration = 40; # in s
phases = 0 # can be [0....# of elements]
amplitude = 0 # can be [0....# of elements]
timePerLocation = 2 # in seconds

###PART2
# Internal Paratmeters
phases = phases = H317Functions.computephasesH317(points_mm, frequencyUS)
totalShotDuration = 1/PRF
shotDuration = dutyCycle/100*totalShotDuration
shotDelay = totalShotDuration - shotDuration
totalShots = int(totalUSDuration/totalShotDuration)
shotsPerLocation = int(timePerLocation/totalShotDuration)
totalLoops = int(totalUSDuration*len(phases)/timePerLocation)
rampingPercent = 0.25
phasesRandom = random.sample(range(0,255), 128)


# Max safe voltage
maxVoltageThreshold = 255 # fus.gen.readAmplitudeThreshold()

# Get masking noise
noise, noise_fs = H317Functions.getmaskingnoise(totalUSDuration+60,frequencyUS,protocol='SHAM')
sd.play(noise, noise_fs)
# Transducer Element Location File
transducerFile = "transducer_Calgary_128.ini"

# IGT 
fus = FUSTHON.FUS()
# utils.initLog(fus, "execNormal")  # uncomment to enable logging in file

listener = utils.ExecListener()
fus.registerListener (listener)

# Opens the connection to the generator (see utils.py for details)
utils.connect(fus)

try:
    trans = transducerXYZ.Transducer()
    if not trans.load(transducerFile):
        print ("Error: can not load the transducer definition from "+transducerFile)
        exit(1)
    channels = trans.channelCount()
    traj = FUSTHON.ElectronicTrajectory(channels)
    shot = FUSTHON.PhaseShot (channels, 1, 1)
    shot.setDuration (int(shotDuration * 10**6), int(shotDelay * 10**6)) # shot duration, shot delay, in us
    shot.setFrequency (0, int(frequencyUS))     # set frequency[0] = 700 KHz, in Hz
    shot.setAmplitude (0, int(0))              # s0 for sham
    shot.setPhases(phasesRandom)                       # set phase[0] = 0  (values in [0,255] = [0,360]deg)
    traj.addShot (shot)
    totalTime = time.time()

# Set up trajectory execuetion information
    trajBuffer = 0
    execCount = int(1)
    execDelayUs = 0  # 1 s, microseconds between trajectory executions
    execMode = FUSTHON.ElecExecMode.REPEAT # Repeat mode allows for higher PRF

    if len(phases) > 1:
        # Send and execute the trajectory
        fus.gen.sendTrajectory (trajBuffer, traj, execMode)
        fus.gen.executeTrajectory (trajBuffer, execCount, execDelayUs)
        time.sleep(totalUSDuration*len(phases)+2) # wait for total duration times number of locations seconds to mimic actual stimulation and 3 seconds time to account for the change in execuetion

    else:
        fus.gen.sendTrajectory (trajBuffer, traj, execMode)
        fus.gen.executeTrajectory (trajBuffer, execCount, execDelayUs)
        time.sleep(totalUSDuration)
    print("Total Time: " + str(time.time() - totalTime))

except Exception as why:
    fus.unregisterListener(listener)
    fus.disconnect()
    print ("Exception: "+str(why))
except KeyboardInterrupt:
    print ("User Interruption")
    fus.unregisterListener(listener)
    fus.disconnect()

fus.unregisterListener(listener)
fus.disconnect()
sd.stop()
