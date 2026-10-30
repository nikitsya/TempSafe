from gpiozero import LED
from time import sleep

led = LED(18)

try:
    print("Normal: off")
    led.off()
    sleep(5)

    print("Warning / Alert: on")
    led.on()
    sleep(5)
    led.off()

    print("Sensor error: two flashes and a pause")
    for _ in range(5):
        led.on()
        sleep(0.2)
        led.off()
        sleep(0.2)
        led.on()
        sleep(0.2)
        led.off()
        sleep(1)

finally:
    led.off()
    led.close()
