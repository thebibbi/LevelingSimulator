# ESP32 Firmware Development Guide

Complete guide for implementing the platform leveling controller on ESP32 hardware.

## 📋 Overview

This firmware implements the control logic for the platform leveling system, including:
- BNO055 IMU reading via I²C
- Inverse kinematics calculations
- PWM motor control
- Position feedback processing
- Safety features
- Serial communication protocol

## 🛠️ Development Environment Setup

### Option 1: Arduino IDE (Recommended for Beginners)

1. **Install Arduino IDE** (version 2.0+)
   - Download from: https://www.arduino.cc/en/software

2. **Install ESP32 Board Support**
   - Go to File → Preferences
   - Add to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools → Board → Board Manager
   - Search "esp32" and install "ESP32 by Espressif Systems"

3. **Install Required Libraries**
   - Tools → Manage Libraries
   - Install:
     - "Adafruit BNO055" by Adafruit
     - "Adafruit Unified Sensor" by Adafruit
     - "ArduinoJson" (for configuration)

### Option 2: PlatformIO (Recommended for Advanced)

1. **Install VS Code** + PlatformIO extension

2. **Create platformio.ini:**
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps = 
    adafruit/Adafruit BNO055@^1.6.0
    adafruit/Adafruit Unified Sensor@^1.1.7
    bblanchon/ArduinoJson@^6.21.0
monitor_speed = 115200
```

## 📁 Firmware Structure

```
esp32-firmware/
├── src/
│   ├── main.cpp                    # Main program
│   ├── imu_sensor.cpp/.h          # IMU interface
│   ├── inverse_kinematics.cpp/.h  # IK solver
│   ├── actuator_control.cpp/.h    # Motor control
│   ├── serial_protocol.cpp/.h     # Communication
│   ├── safety_monitor.cpp/.h      # Safety checks
│   └── config.h                   # Configuration
├── platformio.ini                  # PlatformIO config
└── README.md
```

## 💻 Core Firmware Components

### 1. Configuration (config.h)

```cpp
// config.h
#ifndef CONFIG_H
#define CONFIG_H

// Platform Configuration
#define PLATFORM_TYPE TRIPOD  // or STEWART_3DOF, STEWART_6DOF
#define NUM_ACTUATORS 3       // 3 for tripod, 6 for Stewart

// Platform Dimensions (in meters)
#define PLATFORM_LENGTH 1.83f
#define PLATFORM_WIDTH  1.22f
#define MIN_HEIGHT      0.30f
#define MAX_HEIGHT      0.70f
#define ACTUATOR_STROKE 0.40f

// Pin Definitions
#define SDA_PIN 21
#define SCL_PIN 22

// Actuator 1
#define ACT1_PWM_PIN   25
#define ACT1_DIR_PIN   26
#define ACT1_FB_PIN    34  // Analog feedback
#define ACT1_MIN_PIN   35  // Min limit switch
#define ACT1_MAX_PIN   32  // Max limit switch

// Actuator 2
#define ACT2_PWM_PIN   27
#define ACT2_DIR_PIN   14
#define ACT2_FB_PIN    36
#define ACT2_MIN_PIN   39
#define ACT2_MAX_PIN   33

// Actuator 3
#define ACT3_PWM_PIN   12
#define ACT3_DIR_PIN   13
#define ACT3_FB_PIN    4
#define ACT3_MIN_PIN   15
#define ACT3_MAX_PIN   2

// PWM Configuration
#define PWM_FREQ     1000   // 1 kHz
#define PWM_RES      8      // 8-bit resolution (0-255)

// Control Parameters
#define LEVEL_THRESHOLD  2.0f    // degrees
#define UPDATE_RATE_MS   100     // 10 Hz
#define DEADBAND        0.5f    // degrees
#define MAX_TILT        16.0f   // degrees

// Safety
#define MAX_CURRENT     5.0f    // Amps per actuator
#define WATCHDOG_TIMEOUT 5000   // ms

#endif
```

### 2. IMU Interface (imu_sensor.h)

```cpp
// imu_sensor.h
#ifndef IMU_SENSOR_H
#define IMU_SENSOR_H

#include <Adafruit_BNO055.h>
#include <Wire.h>

class IMUSensor {
public:
    IMUSensor();
    bool begin();
    bool calibrate();
    bool update();
    
    float getRoll() const { return roll; }
    float getPitch() const { return pitch; }
    float getYaw() const { return yaw; }
    float getTiltMagnitude() const;
    
    bool isCalibrated() const { return calibrated; }
    uint8_t getCalibrationStatus();
    
private:
    Adafruit_BNO055 bno;
    float roll, pitch, yaw;
    float roll_offset, pitch_offset, yaw_offset;
    bool calibrated;
    
    void setOffsets(float r, float p, float y);
};

#endif
```

### 3. Actuator Control (actuator_control.h)

```cpp
// actuator_control.h
#ifndef ACTUATOR_CONTROL_H
#define ACTUATOR_CONTROL_H

#include <Arduino.h>

struct ActuatorConfig {
    uint8_t pwm_pin;
    uint8_t dir_pin;
    uint8_t fb_pin;
    uint8_t min_switch_pin;
    uint8_t max_switch_pin;
    uint8_t pwm_channel;
};

class Actuator {
public:
    Actuator(ActuatorConfig config);
    void begin();
    void setTarget(float position_mm);
    void update();
    void stop();
    void enable(bool en);
    
    float getPosition() const { return current_position; }
    float getTarget() const { return target_position; }
    bool isMinLimit() const { return min_limit; }
    bool isMaxLimit() const { return max_limit; }
    bool isEnabled() const { return enabled; }
    float getCurrent() const { return current_draw; }
    
private:
    ActuatorConfig config;
    float current_position;  // mm
    float target_position;   // mm
    float speed;            // mm/s
    bool enabled;
    bool min_limit;
    bool max_limit;
    float current_draw;     // Amps
    
    void readPosition();
    void readLimitSwitches();
    void updateMotor();
    int calculatePWM(float error);
};

class ActuatorController {
public:
    ActuatorController(int num_actuators);
    void begin();
    void setTargets(float* positions_mm);
    void update();
    void emergencyStop();
    void enable(bool en);
    
    Actuator* getActuator(int index) { return &actuators[index]; }
    int getNumActuators() const { return num_actuators; }
    
private:
    Actuator* actuators;
    int num_actuators;
    bool emergency_stop_active;
};

#endif
```

### 4. Inverse Kinematics (inverse_kinematics.h)

```cpp
// inverse_kinematics.h
#ifndef INVERSE_KINEMATICS_H
#define INVERSE_KINEMATICS_H

#include <Arduino.h>

struct Vector3 {
    float x, y, z;
    Vector3(float x = 0, float y = 0, float z = 0) : x(x), y(y), z(z) {}
};

struct Matrix3x3 {
    float m[3][3];
    void identity();
    void multiply(const Matrix3x3& other);
    Vector3 multiply(const Vector3& v);
};

class InverseKinematics {
public:
    InverseKinematics(float length, float width, float min_h, float max_h);
    
    bool solve(float roll, float pitch, float yaw,
               float* actuator_lengths);
    
    bool levelPlatform(float measured_roll, float measured_pitch,
                       float measured_yaw, float* actuator_lengths);
    
private:
    float platform_length;
    float platform_width;
    float min_height;
    float max_height;
    
    Vector3* base_points;
    Vector3* platform_points;
    int num_actuators;
    
    Matrix3x3 rotationMatrix(float roll, float pitch, float yaw);
    float calculateLength(const Vector3& base, const Vector3& platform);
    bool isValid(float length);
};

#endif
```

### 5. Main Program (main.cpp skeleton)

```cpp
// main.cpp
#include <Arduino.h>
#include "config.h"
#include "imu_sensor.h"
#include "actuator_control.h"
#include "inverse_kinematics.h"
#include "serial_protocol.h"
#include "safety_monitor.h"

// Global objects
IMUSensor imu;
ActuatorController actuators(NUM_ACTUATORS);
InverseKinematics ik(PLATFORM_LENGTH, PLATFORM_WIDTH, 
                     MIN_HEIGHT, MAX_HEIGHT);
SerialProtocol serial_comm;
SafetyMonitor safety;

// State variables
bool leveling_enabled = false;
bool auto_level_mode = false;
unsigned long last_update = 0;

void setup() {
    Serial.begin(115200);
    Serial.println("Platform Leveling System - ESP32");
    Serial.println("================================");
    
    // Initialize I2C
    Wire.begin(SDA_PIN, SCL_PIN);
    
    // Initialize IMU
    if (!imu.begin()) {
        Serial.println("ERROR: Failed to initialize IMU!");
        while(1) delay(10);
    }
    Serial.println("IMU initialized");
    
    // Initialize actuators
    actuators.begin();
    Serial.println("Actuators initialized");
    
    // Setup watchdog timer
    safety.begin();
    
    Serial.println("\nSystem ready!");
    Serial.println("Commands: E=Enable, D=Disable, L=Level, C=Calibrate");
}

void loop() {
    unsigned long current_time = millis();
    
    // Update IMU
    imu.update();
    
    // Process serial commands
    serial_comm.processCommands();
    
    // Safety checks
    if (!safety.check(&actuators, &imu)) {
        actuators.emergencyStop();
        leveling_enabled = false;
        Serial.println("SAFETY: Emergency stop triggered!");
    }
    
    // Auto-leveling logic
    if (auto_level_mode && leveling_enabled && 
        (current_time - last_update >= UPDATE_RATE_MS)) {
        
        performLeveling();
        last_update = current_time;
    }
    
    // Update actuators
    actuators.update();
    
    // Feed watchdog
    safety.feed();
    
    delay(10);
}

void performLeveling() {
    float roll = radians(imu.getRoll());
    float pitch = radians(imu.getPitch());
    float yaw = radians(imu.getYaw());
    
    float tilt = imu.getTiltMagnitude();
    
    // Check if leveling needed
    if (tilt < LEVEL_THRESHOLD) {
        return;  // Already level enough
    }
    
    // Calculate required actuator positions
    float actuator_lengths[NUM_ACTUATORS];
    bool valid = ik.levelPlatform(roll, pitch, yaw, actuator_lengths);
    
    if (!valid) {
        Serial.println("ERROR: Cannot level - outside limits!");
        return;
    }
    
    // Convert meters to mm and set targets
    float targets_mm[NUM_ACTUATORS];
    for (int i = 0; i < NUM_ACTUATORS; i++) {
        targets_mm[i] = actuator_lengths[i] * 1000.0f;
    }
    
    actuators.setTargets(targets_mm);
}
```

## 🔧 Implementation Steps

### Phase 1: Basic Testing (1-2 days)
1. Test ESP32 board with Arduino IDE
2. Test I²C communication with BNO055
3. Read IMU orientation data
4. Test single actuator control (PWM + direction)
5. Test position feedback reading

### Phase 2: Integration (2-3 days)
1. Implement inverse kinematics calculations
2. Test IK solver with known angles
3. Integrate multiple actuator control
4. Test coordinated movement

### Phase 3: Leveling Logic (1-2 days)
1. Implement auto-leveling algorithm
2. Add deadband and threshold logic
3. Test leveling response
4. Tune PID/control parameters if needed

### Phase 4: Safety & Polish (1-2 days)
1. Implement limit switch protection
2. Add emergency stop functionality
3. Implement watchdog timer
4. Add status LEDs
5. Create calibration routine

### Phase 5: Field Testing (1 week)
1. Test with actual vehicle
2. Test various terrain angles
3. Verify weather resistance
4. Document any issues
5. Fine-tune parameters

## 📊 Serial Communication Protocol

### Message Format (Binary)

```
[START_BYTE][COMMAND][LENGTH][DATA...][CHECKSUM]

START_BYTE: 0xAA
COMMAND: 1 byte (command ID)
LENGTH: 1 byte (data length)
DATA: Variable length
CHECKSUM: 1 byte (sum of all bytes & 0xFF)
```

### Command Definitions

```cpp
// Commands from PC to ESP32
#define CMD_SET_TARGET      0x01
#define CMD_ENABLE          0x02
#define CMD_EMERGENCY_STOP  0x03
#define CMD_GET_STATUS      0x04
#define CMD_CALIBRATE       0x05
#define CMD_SET_SPEED       0x06

// Responses from ESP32 to PC
#define RESP_STATUS         0x10
#define RESP_ACK            0x11
#define RESP_ERROR          0x12
```

### Example Messages

**Set Targets (3 actuators):**
```
[0xAA][0x01][12][float1][float2][float3][checksum]
12 bytes = 3 floats × 4 bytes each
```

**Enable Actuators:**
```
[0xAA][0x02][1][0x01][checksum]
0x01 = enable, 0x00 = disable
```

**Get Status:**
```
[0xAA][0x04][0][checksum]
```

## 🐛 Debugging Tips

### Serial Debugging
```cpp
#define DEBUG_LEVEL 2  // 0=none, 1=errors, 2=info, 3=verbose

#if DEBUG_LEVEL >= 2
  Serial.print("Position: ");
  Serial.println(position);
#endif
```

### Common Issues

**IMU Not Found:**
- Check I²C connections (SDA, SCL, GND, VCC)
- Verify address (usually 0x28 or 0x29)
- Add pull-up resistors (4.7kΩ) if needed

**Actuators Not Moving:**
- Check PWM signal with oscilloscope
- Verify H-bridge enable pins
- Check power supply current capacity
- Test motor driver separately

**Position Feedback Errors:**
- Calibrate ADC readings
- Check potentiometer wiper connection
- Add filtering for noisy readings

**Leveling Oscillation:**
- Increase deadband
- Add rate limiting
- Tune control gains
- Add damping

## 🔐 Safety Implementation

### Critical Safety Features

```cpp
// safety_monitor.cpp
bool SafetyMonitor::check(ActuatorController* acts, IMUSensor* imu) {
    // Check 1: Tilt angle limits
    if (imu->getTiltMagnitude() > MAX_TILT) {
        return false;
    }
    
    // Check 2: Limit switches
    for (int i = 0; i < acts->getNumActuators(); i++) {
        if (acts->getActuator(i)->isMinLimit() || 
            acts->getActuator(i)->isMaxLimit()) {
            // Limit reached - prevent further movement
        }
    }
    
    // Check 3: Current monitoring
    for (int i = 0; i < acts->getNumActuators(); i++) {
        if (acts->getActuator(i)->getCurrent() > MAX_CURRENT) {
            return false;  // Overcurrent detected
        }
    }
    
    // Check 4: Watchdog
    if (millis() - last_feed > WATCHDOG_TIMEOUT) {
        return false;  // Watchdog timeout
    }
    
    return true;  // All checks passed
}
```

## 📝 Next Steps

1. **Start with simulation:** Test Python code first
2. **Build test rig:** Single actuator on bench
3. **Develop incrementally:** One feature at a time
4. **Test thoroughly:** Safety first!
5. **Document:** Keep notes of issues and solutions

## 📚 Additional Resources

- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)
- [BNO055 Datasheet](https://www.bosch-sensortec.com/products/smart-sensors/bno055/)
- [Adafruit BNO055 Guide](https://learn.adafruit.com/adafruit-bno055-absolute-orientation-sensor)
- [ESP32 PWM Tutorial](https://randomnerdtutorials.com/esp32-pwm-arduino-ide/)

## 🆘 Support

For ESP32-specific issues:
- ESP32 Forum: https://www.esp32.com/
- Arduino Forum: https://forum.arduino.cc/
- PlatformIO Community: https://community.platformio.org/
