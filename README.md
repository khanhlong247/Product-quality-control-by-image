# Lập trình nhúng - Nhóm 10

## Thành viên:

**Trương Long Khánh - 22010198**

**Lưu Mai Tuyết - 22010226**

**Trần Hoàng Hiệp - 22010389**

## Đề tài: Xây dựng hệ thống kiểm soát chất lượng sản phẩm bằng hình ảnh

### 1. Lý do chọn đề tài

### 2. Nội dung đề tài

  Dự án tập trung vào việc phát triển một hệ thống điều khiển kiểm soát chất lượng sản phẩm bằng hình ảnh, với Raspberry Pi 4 đóng vai trò là bộ điều khiển trung tâm. Hệ thống cho phép tự động hoá chụp ảnh và nhận diện sản phẩm, cũng như là theo dõi kết quả thông qua màn hình và cơ cấu phân loại sản phẩm.

  Hệ thống sử dụng kết nối không dây để truyền các tín hiệu và hình ảnh. Nhờ đó, hệ thống tối ưu hơn về thiết kế phần cứng khi sử dụng số lượng dây tối thiểu và tránh được một số lỗi đường truyền liên quan đến dây điện kết nối cũng như là tiết kiệm năng lượng hơn.

  Một điểm nổi bật của dự án là khả năng triển khai nhanh chóng hệ thống trên các máy tính Rasberry Pi khác. Hệ thống nhận diện sản phẩm sẽ được đóng gói thành một Docker container, giúp cho các mạch Raspberry Pi khác có thể chạy mô hình nhận diện sản phẩm mà không cần cài đặt thủ công các thư viện xử lý hình ảnh. 

  Ngoài ra, hệ thống còn hỗ trợ tự động hoá một số tác vụ dựa trên cảm biến, ví dụ như tự động chụp ảnh khi nhận diện sản phẩm ở trong tầm chụp ảnh bằng cảm biến siêu âm, có thể ngắt hệ thống bằng nút bấm khi cần, giúp giảm tiêu thụ điện năng.

  Tổng thể, hệ thống nhận diện chất lượng sản phẩm bằng hình ảnh không chỉ tự động hoá công việc đánh giá chất lượng sản phẩm mà còn giúp quản lý năng lượng một cách hiệu quả, đồng thời tối ưu hoá thiết kế của hệ thống.

### 3. Thiết kế hệ thống

#### a. Phần cứng

-	1 mạch Raspberry Pi.
  
-	1 module ESP32-Cam.
  
-	1 Breadboard.
  
-	1 đèn LED.
  
-	1 màn hình OLED12864 0.96 Inch.
  
-	1 cảm biến siêu âm HC-SR04.
  
-	1 nút nhấn
  
-	2 Servo.
  
-	1 điện trở 220Ω, 1 điện trở 1kΩ, 1 điện trở 1.5kΩ.

#### b. Phần mềm

- Hệ điều hành Rasberry Pi OS 64-bit.
  
-	Arduino IDE để lập trình module ESP32-Cam.
  
-	Bất kỳ phần mềm nào có thể lập trình và chạy chương trình python trên Raspberry Pi OS 64-bit.

- Giao thức truyền thông: Dự án sử dụng giao thức truyền thông MQTT (Message Queuing Telemetry Transpot) để truyền và nhận tín hiệu cũng như hình ảnh giữa Raspberry Pi và ESP32-Cam. Đây là một giao thức nhắn tin nhẹ, hoạt động theo mô hình publish/subscribe, thích hợp cho các ứng dụng IoT.

- Công nghệ đóng gói: Dự án sử dụng công nghệ Docker Containerization để container hoá cho phép đóng gói mô hình nhận diện lá bài sau khi training để chạy trên thiết bị Raspberry Pi và thiết lập môi trường  thực thi để có thể triển khai dễ dàng khi sử dụng ở một mạch Raspberry Pi khác.

### 4. Quy trình hoạt động

![Sơ đồ hoạt động](https://imgur.com/Tpkair2.png)

**UC1 - Nạp sản phẩm:** Servo liên tục xoay để nạp lá bài mới vào vị trí chụp ảnh.

**UC2 - Đo lường vị trí của lá bài:** Cảm biến siêu âm HC-SR04 đóng vai trò liên tục đo vị trí giữa cảm biến và lá bài. Các giá trị này được cảm biến thu thập thường xuyên và gửi về Raspberry Pi để xử lý, đảm bảo rằng hệ thống luôn nhận được thông tin cập nhật về trạng thái lá bài đã được đặt vào vị trí chụp ảnh hay chưa.

**UC3 - Xử lý thông tin cảm biến:** Raspberry Pi 4 sẽ nhận dữ liệu từ cảm biến siêu âm HC-SR04 và so sánh với mốc khoảng cách được chỉ định để nhận biết lá bài đã ở đúng vị trí hay chưa. Dựa trên sự so sánh này, hệ thống sẽ quyết định hành động tiếp theo. Nếu lá bài đã ở vị trí phù hợp thì sẽ chụp ảnh lá bài, ngược lại, nếu không có lá bài nào ở vị trí chụp ảnh thì sẽ tiếp tục đọc giá trị gửi tới từ cảm biến.

**UC4 - Chụp ảnh sản phẩm:** Khi lá bài đã ở trong vị trí chụp ảnh, cảm biến siêu âm sẽ gửi tín hiệu cho Raspberry Pi, Raspberry Pi sẽ bật đèn LED, đồng thời gửi tín hiệu cho ESP32-Cam. Khi ESP32-Cam nhận được tín hiệu từ Raspberry Pi, ESP32-Cam sẽ chụp ảnh lá bài, sau đó gửi hình ảnh tới Raspberry Pi.

**UC5.1 - Xử lý hình ảnh sản phẩm:** Sau khi Raspberry Pi nhận được hình ảnh từ ESP32-Cam, ảnh sẽ được đưa vào mô hình phân loại sản phẩm.

**UC5.2 - Hiển thị thông tin:** Sau khi bức ảnh được nhận diện và phân loại, thông tin về bức ảnh sẽ được hiển thị lên màn hình OLED, từ đó người dùng có thể theo dõi kết quả.

**UC6 - Phân loại sản phẩm:** Sau khi có kết quả phân loại, Servo sẽ xoay để đưa lá bài tới vị trí phân loại phù hợp.

**UC7 - Tương tác người dùng:** Người dùng có thể thao tác ngắt hệ thống qua nút bấm, và cũng có thể khiến hệ thống hoạt động lại bằng cách ấn lần nữa.

### 5. Sơ đồ mạch điện

![Sơ đồ mạch điện](https://imgur.com/6jVW38Q.png)

**Các nút bấm được kết nối với Raspberry Pi để thực hiện các chức năng điều khiển khác nhau:**

•	Nút bấm kết nối với GPIO 12, cho phép người dùng ngắt chương trình và khởi động lại chương trình.

•	Đèn LED kết nối với GPIO 24, hiển thị trạng thái của lá bài.

•	Chân Signal của Servo1 kết nối với GPIO 21, để tự động đưa lá bài vào vị trí chụp ảnh.

•	Chân Signal của Servo2 kết nối với GPIO 20, để tự động phân loại lá bài sau khi nhận diện.

•	Chân SDA, SCL của màn hình OLED12864 được kết nối lần lượt với GPIO 2, GPIO 3 là 2 chân hỗ trợ kết nối I2C của mạch Raspberry Pi 4.

•	Chân Trigger của cảm biến siêu âm HC-SR04 kết nối với GPIO 23.

•	Chân Echo của cảm biến siêu âm HC-SR04 kết nối với GPIO 18.

-	Chân Echo của cảm biến siêu âm được kết nối với mạch Raspberry Pi qua 1 mạch phân áp (voltage divider) để giảm mức điện áp từ 5V của chân Echo xuống còn 3.3V cho chân GPIO của Raspberry Pi. Mục địch tránh hư hỏng mạch Raspberry Pi. Mạch phân áp được tạo từ 2 điện trở, điện trở R1 = 1.5kΩ kết nối giữa chân Echo với GPIO 18 và điện trở R2 = 1kΩ kết nối giữa GPIO và GND.

### 6. Hướng dẫn cài đặt

#### a. Cài đặt giao thức MQTT

- Cập nhật danh sách gói

`sudo apt update && sudo apt upgrade -y`

- Cài đặt Mosquitto

```
sudo apt-get install mosquitto -y
sudo apt-get install mosquitto-clients
```

- Thiết lập cài đặt Mosquitto

```
sudo nano /etc/mosquitto/mosquitto.conf
```

Thay thế nội dung trong file mosquitto.conf bằng nội dung:

```
# Place your local configuration in /etc/mosquitto/conf.d/
#
# A full description of the configuration file is at
# /usr/share/doc/mosquitto/examples/mosquitto.conf.example

pid_file /run/mosquitto/mosquitto.pid

persistence true
persistence_location /var/lib/mosquitto/

log_dest file /var/log/mosquitto/mosquitto.log

allow_anonymous false
password_file /etc/mosquitto/pwfile
listener 1883 0.0.0.0

```

- Thiết lập username và password cho MQTT Broker

```
sudo mosquitto_passwd -c /etc/mosquitto/pwfile TYPE_YOUR_USERNAME_HERE
```

- Cài đặt thư viện paho

```
pip3 install paho-mqtt
```

Thay dòng chữ "TYPE_YOUR_USERNAME_HERE" bằng username mong muốn, sau đó nhấn Enter và điền mật khẩu

#### b. Cài đặt và khởi tạo Docker

- Cài đặt Docker trên Raspberry Pi

```
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $(whoami)
```

- Build Docker

```
docker build -t docker_container_name .
```

Có thể thay "docker_container_name" thành "card_classification_app như sau:

```
docker build -t card_classification_app .
```

- Run Docker:

Trong dự án này, thư mục ứng dụng chính có tên **app** được đặt trong thư mục /home/pi

```
docker run --rm -it --device /dev/i2c-1:/dev/i2c-1 -v /home/pi/app/Pictures:/app/Pictures card_classification_app
```
### 7. Một số kết quả

- Cơ cấu cơ khí:

[![Cơ cấu cơ khí](https://imgur.com/UC7xjPP.png)](https://vimeo.com/manage/videos/1067315136/3858cb4fa2)

- Màn hình Terminal và Serial Monitor:

[![Màn hình hiển thị](https://imgur.com/T5AlxoI.png)](https://vimeo.com/manage/videos/1067315191/cdbe5d3c3c)
