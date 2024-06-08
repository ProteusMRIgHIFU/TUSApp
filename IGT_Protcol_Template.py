
import sys
import os
# Change to correct path
sys.path.append('C:\\Users\\HIFUPC\\Documents\\IGTFUS-SDK-1.8.0\\python\\Python39x64')
import FUSTHON
import utils
import H317Functions
import time
import transducerXYZ
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
rampingPercent = 0.9 if (PRF != 1000) else 0 # don't apply ramping for 1000 Hz. PD is too small.


# Max safe voltage
maxVoltageThreshold = int(maxAmplitudeAllowedHardware) # fus.gen.readAmplitudeThreshold()


# Get masking noise
noise, noise_fs = H317Functions.getmaskingnoise(totalUSDuration+60,frequencyUS)
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
   #Setup up channels and voltage threshold
    fus.gen.setAmplitudeThreshold(maxVoltageThreshold)
    channels = trans.channelCount()

    trajectories = []
    # Create new Trajectories for each of the focus location
    for j in range(len(phases)):
        traj = FUSTHON.ElectronicTrajectory(channels)
        shot = FUSTHON.PhaseShot (channels, 1, 1)
        shot.setDuration (int(shotDuration * 10**6), int(shotDelay * 10**6)) # shot duration, shot delay, in us
        shot.setFrequency (0, int(frequencyUS))     # set frequency[0] = 700 KHz, in Hz
        shot.setAmplitude (0, int(amplitude))              # set amplitude[0] = 128 (half amplitude = 128)
        shot.setPhases(phases[j])                       # set phase[0] = 0  (values in [0,255] = [0,360]deg)
        traj.addShot (shot)
        trajectories.append(traj)

    # Set up the ramping of the signal at the beginning and end
    rampingDuration = int(rampingPercent*255/amplitude*(shotDuration * 10**6))
    # Use max allowed duration for ramping for IGT if duration is largert than the duration allowed
    rampingDuration = rampingDuration if (rampingDuration < fus.gen.getMaxRampDuration()) else fus.gen.getMaxRampDuration()

    fus.gen.setShotRampDuration(fus.gen.hasShotRamp(),rampingDuration)
    fus.gen.setShotRampDuration(not fus.gen.hasShotRamp(),rampingDuration)

    totalTime = time.time()

    if len(phases) > 1:
        # Set up trajectory execuetion information
        trajBuffer = 0
        execCount = int(shotsPerLocation)
        execDelayUs = 0  # 1 s, microseconds between trajectory executions
        execMode = FUSTHON.ElecExecMode.REPEAT # Repeat mode allows for higher PRF

        # Execute Sequence
        for totalTimeCount in range(totalLoops):
            # Check time for each trajectory
            # Send and execute the trajectory
            fus.gen.sendTrajectory (trajBuffer, trajectories[totalTimeCount%len(phases)], execMode)
            fus.gen.executeTrajectory (trajBuffer, execCount, execDelayUs)
            listener.waitExecution()
            trajBuffer=(trajBuffer+1)%2
    else:
        trajBuffer = 0
        execCount = int(totalShots)
        execDelayUs = 0  # 1 s, microseconds between trajectory executions
        execMode = FUSTHON.ElecExecMode.REPEAT # Repeat mode allows for higher PRF
        fus.gen.sendTrajectory (trajBuffer, trajectories[0], execMode)
        fus.gen.executeTrajectory (trajBuffer, execCount, execDelayUs)
        listener.waitExecution()

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