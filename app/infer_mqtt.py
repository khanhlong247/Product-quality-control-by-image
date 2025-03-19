import os
import time
import threading
import random
from datetime import datetime

import torch
import torch.nn as nn
import timm
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import torchvision.transforms as transforms
import paho.mqtt.client as mqtt_client

# -------------------------------
# CAU HINH MQTT
# -------------------------------
broker = ''          # Dia chi MQTT Broker (dia chi IP cua Raspberry Pi)
port = 1883
mqtt_topic_image = "dev/image"         # Topic nhan anh tu ESP32-CAM
mqtt_response_topic = "dev/response"     # Topic gui thong bao "Image Received"
client_id = f'subscribe-{random.randint(0, 1000)}'
username = 'khanhlong'
password = 'khanhlong024'

# -------------------------------
# CAU HINH OLED
# -------------------------------
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

serial = i2c(port=1, address=0x3C)
oled_device = ssd1306(serial, rotate=0)
oled_width = oled_device.width    # 128
oled_height = oled_device.height  # 64

cols = 5
rows = -(-53 // cols) 
cell_width = oled_width // cols
cell_height = oled_height // rows

# -------------------------------
# THU MUC LUU ANH
# -------------------------------
save_dir = os.path.join(os.getcwd(), "Pictures")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
processed_dir = os.path.join(save_dir, "processed")
if not os.path.exists(processed_dir):
    os.makedirs(processed_dir)

# -------------------------------
# DINH NGHIA MAPPING CHO TERMINAL
# -------------------------------
idx_to_class_full = {
    0: "Ace of Spades",
    1: "Two of Spades",
    2: "Three of Spades",
    3: "Four of Spades",
    4: "Five of Spades",
    5: "Six of Spades",
    6: "Seven of Spades",
    7: "Eight of Spades",
    8: "Nine of Spades",
    9: "Ten of Spades",
    10: "Jack of Spades",
    11: "Queen of Spades",
    12: "King of Spades",
    13: "Ace of Hearts",
    14: "Two of Hearts",
    15: "Three of Hearts",
    16: "Four of Hearts",
    17: "Five of Hearts",
    18: "Six of Hearts",
    19: "Seven of Hearts",
    20: "Eight of Hearts",
    21: "Nine of Hearts",
    22: "Ten of Hearts",
    23: "Jack of Hearts",
    24: "Queen of Hearts",
    25: "King of Hearts",
    26: "Ace of Diamonds",
    27: "Two of Diamonds",
    28: "Three of Diamonds",
    29: "Four of Diamonds",
    30: "Five of Diamonds",
    31: "Six of Diamonds",
    32: "Seven of Diamonds",
    33: "Eight of Diamonds",
    34: "Nine of Diamonds",
    35: "Ten of Diamonds",
    36: "Jack of Diamonds",
    37: "Queen of Diamonds",
    38: "King of Diamonds",
    39: "Ace of Clubs",
    40: "Two of Clubs",
    41: "Three of Clubs",
    42: "Four of Clubs",
    43: "Five of Clubs",
    44: "Six of Clubs",
    45: "Seven of Clubs",
    46: "Eight of Clubs",
    47: "Nine of Clubs",
    48: "Ten of Clubs",
    49: "Jack of Clubs",
    50: "Queen of Clubs",
    51: "King of Clubs",
    52: "Joker"
}

# -------------------------------
# DINH NGHIA MAPPING CHO OLED (TEN VIET TAT)
# -------------------------------
idx_to_class_short = {
    0: "1s",
    1: "2s",
    2: "3s",
    3: "4s",
    4: "5s",
    5: "6s",
    6: "7s",
    7: "8s",
    8: "9s",
    9: "10s",
    10: "11s",
    11: "12s",
    12: "13s",
    13: "1h",
    14: "2h",
    15: "3h",
    16: "4h",
    17: "5h",
    18: "6h",
    19: "7h",
    20: "8h",
    21: "9h",
    22: "10h",
    23: "11h",
    24: "12h",
    25: "13h",
    26: "1d",
    27: "2d",
    28: "3d",
    29: "4d",
    30: "5d",
    31: "6d",
    32: "7d",
    33: "8d",
    34: "9d",
    35: "10d",
    36: "11d",
    37: "12d",
    38: "13d",
    39: "1c",
    40: "2c",
    41: "3c",
    42: "4c",
    43: "5c",
    44: "6c",
    45: "7c",
    46: "8c",
    47: "9c",
    48: "10c",
    49: "11c",
    50: "12c",
    51: "13c",
    52: "JK"
}

# -------------------------------
# DINH NGHIA DICTIONARY OLED (su dung mapping cho OLED)
# -------------------------------
oled_cards = { name: 0 for name in idx_to_class_short.values() }

def update_oled():
    """Cap nhat man hinh OLED voi thong tin trong dictionary oled_cards."""
    from PIL import ImageDraw
    image = Image.new("1", (oled_width, oled_height))
    draw = ImageDraw.Draw(image)
    font_size = 7
    font = ImageFont.load_default()  # Su dung font mac dinh
    sorted_items = sorted(oled_cards.items(), key=lambda x: x[0])
    for idx, (card, count) in enumerate(sorted_items):
        col = idx % cols
        row = idx // cols
        x = col * cell_width
        y = row * cell_height
        text = f"{card}:{count}"
        draw.text((x, y), text, font=font, fill=255)
    oled_device.display(image)

update_oled()

# -------------------------------
# MQTT SUBSCRIBER: NHAN ANH
# -------------------------------
def connect_mqtt():
    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print("Successfully connected to MQTT Broker!")
            client.subscribe(mqtt_topic_image)
        else:
            print(f"Failed to connect, reason code {reason_code}")
    client = mqtt_client.Client(client_id=client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def on_message(client, userdata, msg):
    if msg.topic == mqtt_topic_image:
        print("Image message received via MQTT")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"image_{timestamp}.jpg")
        try:
            with open(filename, "wb") as f:
                f.write(msg.payload)
            print(f"Image saved to {filename}")
            result = client.publish(mqtt_response_topic, "Image Received")
            if result[0] == 0:
                print("Notification sent: Image Received")
            else:
                print("Failed to send notification message")
        except Exception as e:
            print("Error saving image:", e)

def mqtt_loop():
    client = connect_mqtt()
    client.on_message = on_message
    client.loop_forever()

mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

# -------------------------------
# MODEL NHAN DIEN ANH
# -------------------------------
class SimpleCardClassifier(nn.Module):
    def __init__(self, num_classes=53):
        super(SimpleCardClassifier, self).__init__()
        self.base_model = timm.create_model('efficientnet_b0', pretrained=True)
        self.features = nn.Sequential(*list(self.base_model.children())[:-1])
        enet_out_size = 1280
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(enet_out_size, num_classes)
        )
    def forward(self, x):
        x = self.features(x)
        output = self.classifier(x)
        return output

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SimpleCardClassifier(num_classes=53)
model.load_state_dict(torch.load("model.pth", map_location=device))
model.to(device)
model.eval()
print("Model loaded and set to eval mode.")

# -------------------------------
# DINH NGHIA TRANSFORM
# -------------------------------
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])

# -------------------------------
# DINH NGHIA MAPPING CHO TERMINAL
# -------------------------------
idx_to_class_full = {
    0: "Ace of Spades",
    1: "Two of Spades",
    2: "Three of Spades",
    3: "Four of Spades",
    4: "Five of Spades",
    5: "Six of Spades",
    6: "Seven of Spades",
    7: "Eight of Spades",
    8: "Nine of Spades",
    9: "Ten of Spades",
    10: "Jack of Spades",
    11: "Queen of Spades",
    12: "King of Spades",
    13: "Ace of Hearts",
    14: "Two of Hearts",
    15: "Three of Hearts",
    16: "Four of Hearts",
    17: "Five of Hearts",
    18: "Six of Hearts",
    19: "Seven of Hearts",
    20: "Eight of Hearts",
    21: "Nine of Hearts",
    22: "Ten of Hearts",
    23: "Jack of Hearts",
    24: "Queen of Hearts",
    25: "King of Hearts",
    26: "Ace of Diamonds",
    27: "Two of Diamonds",
    28: "Three of Diamonds",
    29: "Four of Diamonds",
    30: "Five of Diamonds",
    31: "Six of Diamonds",
    32: "Seven of Diamonds",
    33: "Eight of Diamonds",
    34: "Nine of Diamonds",
    35: "Ten of Diamonds",
    36: "Jack of Diamonds",
    37: "Queen of Diamonds",
    38: "King of Diamonds",
    39: "Ace of Clubs",
    40: "Two of Clubs",
    41: "Three of Clubs",
    42: "Four of Clubs",
    43: "Five of Clubs",
    44: "Six of Clubs",
    45: "Seven of Clubs",
    46: "Eight of Clubs",
    47: "Nine of Clubs",
    48: "Ten of Clubs",
    49: "Jack of Clubs",
    50: "Queen of Clubs",
    51: "King of Clubs",
    52: "Joker"
}

# -------------------------------
# VONG LAP PHAN LOAI ANH
# -------------------------------
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
servo_pin = 21
GPIO.setup(servo_pin, GPIO.OUT)
servo = GPIO.PWM(servo_pin, 50)  # 50Hz
def set_servo(angle):
    duty = 7.5 + ((angle - 90) / 18)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)

servo.start(7.5)  # Dat servo o 90 do (trung tinh)

def classification_loop():
    print("Starting classification loop...")
    while True:
        image_files = [f for f in os.listdir(save_dir)
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                       and os.path.isfile(os.path.join(save_dir, f))]
        if not image_files:
            time.sleep(1)
            continue

        for img_file in image_files:
            img_path = os.path.join(save_dir, img_file)
            if not os.path.exists(img_path):
                print(f"File {img_path} does not exist. Skipping.")
                continue

            try:
                img = Image.open(img_path).convert("RGB")
            except Exception as e:
                print(f"Error opening image {img_path}: {e}")
                continue

            # --- Them code dieu chinh chat luong anh ---
            enhancer_contrast = ImageEnhance.Contrast(img) # Tang do tuong phan
            img = enhancer_contrast.enhance(1.7)
            enhancer_brightness = ImageEnhance.Brightness(img) # Tang do sang
            img = enhancer_brightness.enhance(1.5)
            enhancer_sharpness = ImageEnhance.Sharpness(img) # Tang do sac net
            img = enhancer_sharpness.enhance(1.5)
            # ----------------------------------------------

            # Tien xu ly anh va them batch dimension
            img_tensor = transform(img).unsqueeze(0).to(device)

            with torch.no_grad():
                output = model(img_tensor)
            pred_idx = int(torch.argmax(output, dim=1).item())
            card_name_full = idx_to_class_full.get(pred_idx, "Unknown")
            print(f"Image: {img_file} -> Recognized card: {card_name_full}")

            # Dieu khien servo theo ket qua nhan dien
            if card_name_full != "Unknown":
                # Neu la bai thuoc 53 la bai -> quay ve 45 do
                set_servo(45)
            else:
                # Neu la bai la Unknown -> quay ve 135 do
                set_servo(135)
            # Reset servo ve 90 do
            set_servo(90)

            # Cap nhat dictionary OLED voi mapping cho OLED
            card_name_short = idx_to_class_short.get(pred_idx, "Unknown")
            if card_name_short in oled_cards:
                if card_name_short == "JK":
                    if oled_cards[card_name_short] < 2:
                        oled_cards[card_name_short] += 1
                        update_oled()
                else:
                    if oled_cards[card_name_short] == 0:
                        oled_cards[card_name_short] = 1
                        update_oled()

            # Sau khi xu ly, chuyen file anh sang processed_dir de tranh xu ly lai
            new_path = os.path.join(processed_dir, img_file)
            if os.path.exists(img_path):
                try:
                    os.rename(img_path, new_path)
                    print(f"Moved file {img_file} to processed folder.")
                except Exception as e:
                    print(f"Error moving file {img_file}: {e}")
            else:
                print(f"File {img_path} not found when attempting to move.")

        time.sleep(1)

if __name__ == '__main__':
    try:
        classification_loop()
    except KeyboardInterrupt:
        print("Interrupted by user. Cleaning up...")
    finally:
        servo.stop()
        GPIO.cleanup()
