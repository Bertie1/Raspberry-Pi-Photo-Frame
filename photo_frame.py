# Photo frame code ver 1.0
# Copyright (c) 2015 T L Burton
# Credit to Samuel Clay for inspiration, guidance and code snippets

import RPi.GPIO as GPIO
import time
import subprocess as subprocess
import signal as signal
import os as os
import threading as threading

GPIO.setmode(GPIO.BCM)

screen_on = True
KEEP_ALIVE_UNITS = 60                   # Number of seconds per unit for keep alive count 
KEEP_ALIVE = 10                         # Number of units to keep screen on for
screen_counter = KEEP_ALIVE
fbi_str = "fbi -t 180s -u --noverbose /mnt/photos/*.jpg"

# Interupt handler for photo frame covering the following functions
# 1. Set up interupt for power_off switch
# 2. Set up interupt for restart switch
# 3. Handle PIR sensor to ensure screen is on when someone is in room

def int_power_off(channel):             # Shutdown button interupt
	subprocess.call(["shutdown","now"])

def int_restart(channel):               # Restart button interupt
	subprocess.call(["shutdown","-r","now"])

def start_fbi():
	fbi = threading.Thread(target=cmd_fbi)
	fbi.start()

def cmd_fbi():
	os.system(fbi_str)

def kill_fbi():
	proc_no = subprocess.check_output(["pidof","fbi"])
	os.kill(int(proc_no[0:len(proc_no)-1]), signal.SIGKILL)	

def int_movement(channel):              # PIR Interupt
	global screen_on
	global screen_counter

	# Restart screen counter	whenever movement is detected
	screen_counter = KEEP_ALIVE

	# If the screen is off then switch it back on and restart fbi
	if not (screen_on):
		subprocess.call(["tvservice","-p"]) 
		subprocess.call(["fbset","-depth","8"])
		subprocess.call(["fbset","-depth","32"])	
		screen_on = True                          # Set the screen flag to on
		start_fbi()                               # Start fbi

# Main procedure

# Inititalise GPIO
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # Pin 23 - Power off switch
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # Pin 24 - Restart switch
GPIO.setup(18, GPIO.IN)                                   # Pin 18 - PIR 

GPIO.add_event_detect(23, GPIO.FALLING, callback=int_power_off, bouncetime=500)
GPIO.add_event_detect(24, GPIO.FALLING, callback=int_restart, bouncetime=500)
GPIO.add_event_detect(18, GPIO.RISING, callback=int_movement)

# Run fbi for first time
start_fbi()  

# Start eternal loop
while True:
	# Screen heartbeat 
	time.sleep(KEEP_ALIVE_UNITS)
	
	if screen_counter > 0:	
		screen_counter = screen_counter - 1

	if screen_counter == 0:
		kill_fbi()                                             # Stop fbi process
		subprocess.call(["tvservice","-o"])                    # Switch the screen off 
		screen_on = False                                      # Set the screen flag to off
		screen_counter = -1                                    # Only swtich screen off once
