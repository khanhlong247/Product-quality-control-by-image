import random
import time
from time import sleep
from paho.mqtt import client as mqtt_client
from gpiozero import LED, DistanceSensor, Button
import RPi.GPIO as GPIO
import threading

# -------------------------------
# CAU HINH MQTT
# -------------------------------
broker = ''         # Dia chi MQTT Broker (dia chi IP cua Raspberry Pi)
port = 1883
topic = "dev/test"  # Topic gui lenh
client_id = f'publish-{random.randint(0, 1000)}'
username = ''        # Username cua MQTT Broker
password = ''        # Password cua MQTT Broker

# -------------------------------
# CAU HINH PHAN CUNG
# -------------------------------
led = LED(24)
sensor = DistanceSensor(echo=18, trigger=23, max_distance=1, threshold_distance=0.1)
button = Button(12, pull_up=True)

paused = False          # Bien toan cuc luu trang thai pause
current_state = None    # "LED on" hoac "LED off"

# -------------------------------
# CAU HINH SERVO (360 do)
# -------------------------------
GPIO.setmode(GPIO.BCM)
servo_pin = 20
GPIO.setup(servo_pin, GPIO.OUT)
servo = GPIO.PWM(servo_pin, 50)  # Tần số 50Hz
servo.start(7.5)  # Neutral: 7.5% duty cycle

# -------------------------------
# HAM DOI TRANG THAI PAUSE QUA NUT NHAN (debounce)
# -------------------------------
def toggle_pause():
    global paused
    paused = not paused
    if paused:
        print("Chuong trinh da pause. Trang thai hien tai:", current_state)
    else:
        print("Tiep tuc hoat dong. Trang thai tiep tuc:", current_state)
    # Doi den khi nut duoc tha ra de tranh toggle lien tuc
    while button.is_pressed:
        sleep(0.1)
    sleep(0.5)  # debounce delay

button.when_pressed = toggle_pause

# -------------------------------
# HAM KET NOI MQTT
# -------------------------------
def connect_mqtt():
    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, reason code {reason_code}")
    client = mqtt_client.Client(client_id=client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish_state(client, state):
    result = client.publish(topic, state)
    if result[0] == 0:
        print(f"Sent `{state}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

# -------------------------------
# HAM DIEU KHIEN SERVO
# -------------------------------
def servo_control():
    global paused
    neutral = 7.5         # Duty cycle trung tinh
    positive_speed = 10   # Duty cycle de quay theo chieu duong
    rotation_time = 2.0   # Thoi gian quay 180 do
    while True:
        if not paused:
            # Quay 180 do theo chieu duong
            servo.ChangeDutyCycle(positive_speed)
            time.sleep(rotation_time)
            servo.ChangeDutyCycle(neutral)  # Dung servo
            # Cho 8 giay truoc khi quay tiep
            time.sleep(8)
        else:
            # Khi pause, dung servo
            servo.ChangeDutyCycle(neutral)
            time.sleep(0.5)

# -------------------------------
# HAM CHAY CHUONG TRINH CHINH
# -------------------------------
def run():
    global current_state
    client = connect_mqtt()
    client.loop_start()

    # Bat dau chay servo trong mot luong rieng
    servo_thread = threading.Thread(target=servo_control)
    servo_thread.daemon = True
    servo_thread.start()

    try:
        while True:
            if not paused:
                distance = sensor.distance
                # Neu khoang cach <= 0.1 m thi LED on, nguoc lai LED off
                if distance <= 0.1:
                    if current_state != "LED on":
                        led.on()
                        current_state = "LED on"
                        publish_state(client, "LED on")
                else:
                    if current_state != "LED off":
                        led.off()
                        current_state = "LED off"
                        publish_state(client, "LED off")
            sleep(0.5)
    finally:
        client.loop_stop()
        client.disconnect()
        GPIO.cleanup()

if __name__ == '__main__':
    run()
