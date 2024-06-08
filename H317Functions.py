import numpy as np
import scipy.io
import math
from scipy import signal

def computephasesH317(targets_mm, freq):
	'''
	Calculate phases for steering away from the geometric focus

	Keyword arguments:
	targets_mm -- coordinates for steering
	freq -- US freq	
	'''
	SOUND_SPEED_WATER = 1482 #m/s
	transducerElementLocations = np.genfromtxt("H-317 XYZ Coordinates_double_corrected.csv", delimiter = ',')
	transducerElementLocations = transducerElementLocations[1:len(transducerElementLocations):1]
	transducerElementLocations = np.delete(transducerElementLocations,0,1)
	transducerElementLocations = transducerElementLocations *25.4; # mm
	elementAssignment = [49, 34, 33, 17, 2, 1, 113, 98, 97, 81, 66, 65, 50, 51, 35, 36, \
	18, 19, 3, 4, 114, 115, 99, 100, 82, 83, 67, 68, 52, 53, 54, 37, \
	38, 39, 40, 20, 23, 21, 22, 5, 6, 7, 8, 116, 117, 118, 101, 102, \
	103, 104, 84, 85, 86, 69, 70, 71, 72, 55, 56, 57, 41, 42, 43, 44, \
	26, 24, 25, 9, 10, 11, 12, 122, 119, 120, 121, 105, 106, 107, 108, 90, \
	87, 88, 89, 73, 74, 75, 76, 58, 59, 62, 63, 64, 45, 46, 47, 48, \
	28, 27, 29, 30, 31, 32, 13, 14, 15, 16, 124, 125, 123, 126, 127, 128, \
	109, 110, 111, 112, 92, 93, 91, 94, 95, 96, 77,78, 79, 80, 60, 61]
	elementAssignment = [i-1 for i in elementAssignment]
	phases = []
	points_mm = targets_mm
	print(len(points_mm[0]))
	if (len(points_mm[0]) != 3):
		Phase = []
		x = point_mm[0] / 1000.0
		y = point_mm[1] / 1000.0
		z = point_mm[2] / 1000.0
		for i in range(128):
		    elem = transducerElementLocations[i]/1000
		    wavelen = SOUND_SPEED_WATER / freq
		    dist = math.sqrt (math.pow(elem[0]-x,2) + math.pow(elem[1]-y,2) + math.pow(elem[2]-z,2))
		    rem = math.modf(dist / wavelen)[0]
		    phase = int(0.5 + rem * 256.0)
		    Phase.append(phase % 256)
		phasesOk = [0] * len(Phase)
		for i in range(len(elementAssignment)):
		    phasesOk[elementAssignment[i]] = Phase[i]
		phases.append(phasesOk)
	else:
		for point_mm in points_mm:


			print(point_mm)
			Phase = []
			x = point_mm[0] / 1000.0
			y = point_mm[1] / 1000.0
			z = point_mm[2] / 1000.0
			for i in range(128):
			    elem = transducerElementLocations[i]/1000
			    wavelen = SOUND_SPEED_WATER / freq
			    dist = math.sqrt (math.pow(elem[0]-x,2) + math.pow(elem[1]-y,2) + math.pow(elem[2]-z,2))
			    rem = math.modf(dist / wavelen)[0]
			    phase = int(0.5 + rem * 256.0)
			    Phase.append(phase % 256)

			phasesOk = [0] * len(Phase)
			if (point_mm == [0, 0, 0]):
				phases.append(phasesOk)
			else:
				for i in range(len(elementAssignment)):
				    phasesOk[elementAssignment[i]] = Phase[i]
				phases.append(phasesOk)

	return phases

def getmaskingnoise(duration, USFreq = 2.5e5,protocol='LIFU'):
	'''
	create masking noise for US

	Keyword arguments:
	duration -- total duration of the protocol
	USFreq -- US frequency
	protocol -- LIFU
	'''
	# Parameters
	signal_amp = 0.1; # Amplitude
	noise_amp = signal_amp * 2.5
	fs = 48000 # Sampling Frequency (Hz)
	ramp_time = 1.7 # Time for lifu replica sound to start (s)
	burst_freq = 100 # LIFU burst freq (Hz)

	# Time Points
	time_points = np.linspace(0,duration,int(duration*fs)-1)
	ramp_time_point_num = int(ramp_time*fs)-1
	# 250 kHz Sine Wave
	lifu_values = signal_amp*np.sin(2*math.pi*USFreq*time_points)

	# Ramped 250 kHz Sine Wave
	ramped_lifu_values = lifu_values
	ramped_lifu_values[1:ramp_time_point_num] = 0
	ramped_lifu_values[len(ramped_lifu_values)-ramp_time_point_num:len(ramped_lifu_values)] = 0
	# Square Wave
	burst_values = 0.5*signal.square(2*math.pi*burst_freq*time_points, 0.1)+0.5
	# Static Noise
	noise_values = np.random.rand(time_points.shape[0])*noise_amp

	# Final signals
	lifu_signal = lifu_values * burst_values
	lifu_signal_noise = lifu_signal + noise_values
	ramped_lifu_signal = ramped_lifu_values * burst_values; 
	ramped_lifu_signal_noise = ramped_lifu_signal + noise_values

	if protocol == 'LIFU':
		return noise_values, fs
	else:
		return ramped_lifu_signal_noise, fs
