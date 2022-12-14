import RPi.GPIO as GPIO
import logging

logger = logging.getLogger("__main__")

# Relay Module/Pump
pump_pin = 7
sensor_pin = 21


def setup(pump=None, sensor=None):
    logger.debug("Setting up through `teuphlib.setup()`")
    global pump_pin, sensor_pin
    GPIO.setmode(GPIO.BCM)
    if pump:
        pump_pin = pump
    if sensor:
        sensor_pin = sensor
    print("jj")
    GPIO.setup(pump_pin, GPIO.OUT)
    unpump()
    GPIO.setup(sensor_pin, GPIO.IN)

def shutdown():
    logger.debug("Shutting down through `teuphlib.shutdown()`")
    GPIO.cleanup()

def pump():
    # when connected to 3v power, low turns it
    # on and high turns it off (???) yes idk why
    logger.debug("Opening the pump through `teuphlib.pump()`")
    GPIO.output(pump_pin, GPIO.LOW)

def unpump():
    logger.debug("Closing pump through `teuphlib.unpump()`")
    GPIO.output(pump_pin, GPIO.HIGH)

def is_wet() -> bool:
    logger.debug("Checking sensor through `teuphlib.is_wet()`")
    return not GPIO.input(sensor_pin)
