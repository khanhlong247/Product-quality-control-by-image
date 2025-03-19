# Sử dụng base image cho ARM64 (Raspberry Pi OS 64-bit)
FROM arm64v8/python:3.9-slim

# (Tùy chọn) Nếu bạn muốn sử dụng piwheels – thường dành cho ARMv7, với ARM64 bạn có thể sử dụng index mặc định.
# RUN pip config set global.index-url https://www.piwheels.org/simple

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc
WORKDIR /app

# Copy file requirements.txt và cài đặt các gói Python cần thiết
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn (code, file model, thư mục Pictures) vào container
COPY . /app

# Chạy ứng dụng nhận diện ảnh
CMD ["python", "infer_mqtt.py"]
