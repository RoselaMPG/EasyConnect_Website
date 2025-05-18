# EasyConnect
Imagine you're at an event, having a great conversation with a potential connection — vibes are good, ideas are flowing, then suddenly,

"Wait, can I get your contact?" 
"Oh wait! I am not logged in" 
“Sorry, how do you spell your name again?”

Lucky for you (or not), no need to imagine — you’ve likely experienced this before.

What if we can eliminate that awkward process? 

Introducing EasyConnect – a wristband solution that helps you exchange contact info with people you meet at events, all with a simple handshake!


## Overview
- EasyConnect is a wristband solution that streamlines event check-in, check-out, post-event follow up, and event analytics collection while having a user-centric approach and addressing the needs of end-users - a seamless way of connecting. 


## Potential Business Model
- **Rental model**
  - Event hosts can rent our smart wristbands and support infrastructure for a small percentage of the purchase price, somewhere between 5-10% seems reasonable.
- **Purchase model**
  - Event hosts can purchase our smart wristbands and support infrastructure, allowing them to be reused/reprogrammed as desired.


## Hardware

### Microcontroller
- [Tiny Matter-Native Board for Smart Home - XIAO ESP32C6](https://www.seeedstudio.com/XIAO-ESP32C6-p-5854.html)
- Chosen due to networking capabilities and small form factor, specifically the ability to create thread networks.

### Thread Border Router
- [Amazon.com: ESP Thread Border Router/Zigbee Gateway Board](https://www.amazon.com/ESP-Thread-Border-Router-Gateway/dp/B0BN6NP21L)
- Chosen due to compatibility with the microcontroller to create thread networks. Ample information online about how to connect this gateway with the ESP32C6.

### Inertial Measurement Unit
- [Adafruit BNO055 + BMP280 BFF Add-On for QT Py](https://www.adafruit.com/product/4754)
- Chosen due to small form factor and performance capabilities of the BN055 chip which produces high quality data and will allow for simplified gesture recognition.

### Display
- [Adafruit 1.14 240x135 Color TFT Display + MicroSD Card Breakout [ST7789] : ID 4383](https://www.adafruit.com/product/4383)
- Chosen due to it being a high pixel density color display in small form factor with a built in microsd card reader which will allow images to be downloaded without using the built in MCU memory which is extremely limited.

### NFC tag
- [Adafruit ST25DV16K I2C RFID EEPROM Breakout - STEMMA QT / Qwiic : ID 4701](https://www.adafruit.com/product/4701)
- Chosen due to the ability to reprogram the tag over I2C which allows the MCU to reprogram the tag dynamically and it can be read using modern smartphones.

### SD Card
- [Amazon.com: PNY 32GB Elite Class 10 U1 microSDHC Flash Memory Card - 100MB/s, Class 10, U1, Full HD, UHS-I, Micro SD (Pack of 3)](https://www.amazon.com/PNY-Elite-microSDHC-Memory-3-Pack/dp/B07YXJM282)
- Chosen due to the price point, cheapest Micro SD cards I could find from a reputable company.

### External Antenna
- [Amazon.com: Adafruit 2.4GHz Mini Flexible WiFi Antenna with UFL Connector - 100mm](https://www.amazon.com/Adafruit-2-4GHz-Flexible-Antenna-Connector/dp/B00LSYRLK8)
- Chosen due to easy compatibility with the MCU using the UFL connector and the antenna being flexible which will allow it to be stored in the strap of the wristband.

### Battery
- [Amazon.com: KBT 3.7V 500mAh Li-Polymer Battery: 503035 Lipo Rechargeable Lithium-ion Replacement Batteries with PH 1.25 JST Connector, PH2.0/2.54 JST Connector for Replacement](https://www.amazon.com/KBT-503035-Rechargeable-Lithium-ion-Replacement/dp/B0CKGLWRSP)
- Chosen due to it having similar dimensions to the display which is the largest breakout board on the device while providing sufficient capacity. The Apple Watch Ultra series batteries have similar capacities (around 500mAh).

### Wristband Material
- [TPU 85A / TPU 90A | Bambu Lab USA Store (TPU 90A- White)](https://us.store.bambulab.com/products/tpu-85a-tpu-90a)
- Chosen due to it being the most flexible material that I'm able to print with using my 3D printer that isn't a crazy color. Planned to be used as the strap material.
- [PC FR | Bambu Lab USA Store (Black)](https://us.store.bambulab.com/products/pc-fr)
- Chosen due to its flame resistant properties and ability to withstand heat without deformation. Planned to be used as electronic housing.


## Cost Analysis

### Prototyping Phase
- MCU: $5.20
- IMU: $29.95
- Display: $9.95
- NFC Tag: $3.95
- Antenna: $8.16
- Battery: $8.99
- Housing: $2 (Estimation)
- **Total: ~$68.2 per wristband**

### Scaling Phase
- Custom PCB that houses all the chips on a single board which will dramatically bring down the cost when manufacturing at volume and reduce the overall size of the device.
- **100+ units**
  - Processor chip: $2.03
    - [ESP32-C6 Espressif Systems | RF and Wireless | DigiKey](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-C6/15822984)
  - IMU chip: $9.6
    - [BNO055 Bosch Sensortec | Sensors, Transducers | DigiKey](https://www.digikey.com/en/products/detail/bosch-sensortec/BNO055/5922301)
  - Display: $2.93
    - [1.14 inch Color 135x240 IPS TFT LCD Display](https://www.aliexpress.us/item/3256802644457067.html)
  - NFC chip: $0.82
    - [ST25DV16K-IER6T3 STMicroelectronics | RF and Wireless | DigiKey](https://www.digikey.com/en/products/detail/stmicroelectronics/ST25DV16K-IER6T3/10232916)
  - Custom WIFI antenna: 
    - link
  - Custom NFC antenna: 
    - link
  - Custom PCB: 
    - link
  - Custom Lithium-ion battery: 
    - link
  - Custom Injection molded housing: 
    - link
  - **Total: ~$ per wristband**


## Software

- Backend Framework: FastAPI 

- Templating Engine: Jinja2  

- Web Server: Uvicorn  

- Database: MySQL

- Environment Management: python-dotenv  

- Authentication: session-based, with hashed credentials  

- Frontend: Server-rendered HTML with basic navigation (Jinja2 + static HTML/CSS)  

- Containerization: Docker 