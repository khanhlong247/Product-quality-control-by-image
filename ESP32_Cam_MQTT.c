#include <WiFi.h>
#include <PubSubClient.h>
#include <vector>
#include <string>
#include "esp_camera.h"
#include "esp_log.h"

// WiFi configuration
const char *ssid = "";           // Tên Wi-Fi
const char *password = "";      // Mật khẩu Wi-Fi

// MQTT configuration
const char *mqtt_broker = "";          // Địa chỉ MQTT broker (Chính là địa chỉ IP của Raspberry Pi)
const char *mqtt_command_topic = "dev/test";    // Topic nhận tín hiệu
const char *mqtt_image_topic   = "dev/image";     // Topic gửi ảnh
const char *mqtt_username = "";          // Tên người dùng MQTT
const char *mqtt_password = "";         // Mật khâu người dùng MQTT
const int mqtt_port = 1883;

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// Global flags để điều khiển chu trình
bool ledOnState = false;         // true khi nhận được "LED on" và chưa có "LED off" tiếp theo
bool captureImageFlag = false;   // được đặt true khi có chuyển trạng thái từ off sang on
bool responseReceivedFlag = false; // được đặt true khi nhận được phản hồi từ Raspberry Pi

// Hàm khởi tạo camera
void init_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  // Data pins
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;

  // Clock & sync
  config.pin_xclk  = 0;
  config.pin_pclk  = 22;
  config.pin_vsync = 25;
  config.pin_href  = 23;

  // SCCB pins
  config.pin_sccb_sda = 26;
  config.pin_sccb_scl = 27;

  // Power down & reset
  config.pin_pwdn  = 32;
  config.pin_reset = -1;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Cấu hình khung hình, chất lượng JPEG và số lượng frame buffer
  config.frame_size = FRAMESIZE_QVGA; // kích thước ảnh QVGA (320x240)
  config.jpeg_quality = 63; 
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  
  // Chỉnh độ sáng
  s->set_brightness(s, -2);
  // Chỉnh tương phản
  s->set_contrast(s, 2);
  // Chỉnh bão hòa màu
  s->set_saturation(s, -2);

}

// Callback MQTT: xử lý tin nhắn từ các topic được subscribe
void callback(char* topic, byte* payload, unsigned int length) {
  std::string msg((char*)payload, length);
  Serial.printf("Message arrived in topic: %s, message: %s\n", topic, msg.c_str());
  
  // Xử lý tin nhắn từ topic lệnh LED (dev/test)
  if (strcmp(topic, mqtt_command_topic) == 0) {
    if (msg == "LED on") {
      // Nếu chuyển từ LED off sang on thì mới chụp ảnh
      if (!ledOnState) {
        ledOnState = true;
        captureImageFlag = true;
      }
    } else if (msg == "LED off") {
      // Cập nhật trạng thái LED về off để sẵn sàng cho chu kỳ mới
      ledOnState = false;
    }
  }
  // Xử lý tin nhắn phản hồi từ Raspberry Pi
  else if (strcmp(topic, "dev/response") == 0) {
    Serial.printf("Response received: %s\n", msg.c_str());
    responseReceivedFlag = true;
  }
}

void setup() {
  Serial.begin(9600);
  esp_log_level_set("CAM_HAL", ESP_LOG_NONE);
  esp_log_level_set("CAM_SENSOR", ESP_LOG_NONE);
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  
  // Khởi tạo camera với các thiết lập mới
  init_camera();
  
  // Cấu hình MQTT
  client.setServer(mqtt_broker, mqtt_port);
  client.setBufferSize(50000); // Tăng buffer để gửi ảnh
  client.setCallback(callback);
  
  // Kết nối MQTT
  while (!client.connected()) {
    String client_id = "esp32-client-";
    client_id += String(WiFi.macAddress());
    Serial.printf("The client %s connects to the MQTT broker\n", client_id.c_str());
    if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("Connected to MQTT broker");
    } else {
      Serial.print("failed with state ");
      Serial.println(client.state());
      delay(2000);
    }
  }
  
  // Subscribe các topic cần thiết
  client.subscribe(mqtt_command_topic);
  client.subscribe("dev/response");
}

void loop() {
  client.loop();

  // Nếu có yêu cầu chụp ảnh (khi chuyển trạng thái LED từ off sang on)
  if (captureImageFlag) {
    captureImageFlag = false;
    Serial.println("LED on detected. Capturing image...");
    
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      return;
    }
    Serial.printf("Captured image with size: %u bytes\n", fb->len);
    
    if (client.publish(mqtt_image_topic, fb->buf, fb->len)) {
      Serial.println("Image published successfully.");
    } else {
      Serial.println("Failed to publish image.");
    }
    esp_camera_fb_return(fb);
    
    // Sau khi gửi ảnh, chờ phản hồi từ Raspberry Pi trước khi chu kỳ mới
    unsigned long startWait = millis();
    while (!responseReceivedFlag) {
      client.loop();
      if (millis() - startWait > 10000) { // Timeout sau 10 giây
        Serial.println("Response timeout.");
        break;
      }
      delay(10);
    }
    responseReceivedFlag = false; // Reset cờ phản hồi cho chu kỳ mới
  }
}
