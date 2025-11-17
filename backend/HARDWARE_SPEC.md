# Hardware Specifications

Complete bill of materials and specifications for the platform leveling system.

## 📊 Platform Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Dimensions | 1.83m × 1.22m (6' × 4') | Standard RTT size |
| Weight Capacity | 300-450 kg | Includes safety margin |
| Max Tilt Compensation | 15-16° | Each direction |
| Leveling Accuracy | ±2° | Acceptable tolerance |
| Height Range | 300-700mm | Adjustable |

## 🔩 Linear Actuators

### Requirements per Actuator

| Specification | 3-Actuator | 6-Actuator (Stewart) |
|--------------|------------|----------------------|
| Stroke Length | 400mm | 400mm |
| Force Required | 1500-2000N | 800-1000N |
| Speed | 10-20 mm/s | 10-20 mm/s |
| Voltage | 12V DC | 12V DC |
| Current Draw | 3-5A peak | 2-4A peak |
| Duty Cycle | 25% | 25% |

### Recommended Models

#### Budget Option (~$50-80 each):
- **Actuonix L16-100-150-12-P**
  - 150mm stroke (may need longer)
  - 12V, 100:1 gear ratio
  - Built-in potentiometer feedback
  - Good for testing

#### Mid-Range Option (~$120-180 each):
- **Progressive Automations PA-14-8-150**
  - 150-400mm stroke options
  - 12V, 8"/s speed
  - Hall effect position sensor
  - 1500N force
  - **RECOMMENDED FOR MVP**

#### Heavy-Duty Option (~$200-300 each):
- **Firgelli FA-PO-35-12-10**
  - 250mm stroke
  - 12V, heavy duty
  - Optical position feedback
  - 2000N+ force
  - Limit switches included

### Critical Actuator Features:
✅ Position feedback (potentiometer, hall effect, or optical)
✅ Limit switches (mechanical or integrated)
✅ 12V DC operation
✅ Weather resistant (IP65+ for outdoor use)
✅ Self-locking (for safety when unpowered)

## 🧭 IMU Sensor

### Production: BNO055 (Bosch 9-DOF)

**Specifications:**
- 9 degrees of freedom
- 3-axis accelerometer
- 3-axis gyroscope
- 3-axis magnetometer
- Built-in sensor fusion
- I²C/UART interface
- ±2° accuracy (after calibration)
- Operating voltage: 3.3V

**Recommended Module:**
- Adafruit BNO055 Breakout Board (~$35)
- Includes voltage regulator
- Easy I²C interface
- Well-documented library

**Alternative:**
- MPU-6050 (budget option, ~$5)
  - 6-DOF only (no magnetometer)
  - Requires external sensor fusion
  - Less accurate but usable

## 🖥️ Microcontroller: ESP32

### Specifications

**Module:** ESP32-DevKitC or similar
- Dual-core 240 MHz
- 520 KB SRAM
- WiFi + Bluetooth (for future app control)
- Multiple PWM channels (for actuators)
- I²C interface (for IMU)
- ADC inputs (for position feedback)
- Cost: ~$8-15

**Required Peripherals:**
- MicroUSB cable for programming
- 3.3V to 12V level shifters (if needed)
- Protection diodes
- Pull-up resistors for I²C

## ⚡ Motor Drivers (H-Bridge)

### For 3-Actuator System

**Option A: Individual Drivers**
- 3× L298N H-Bridge modules (~$5 each)
  - 2A continuous per channel
  - 3A peak
  - Built-in voltage regulators
  - Enable/direction control
  - **Good for MVP testing**

**Option B: Integrated Solution**
- Pololu Dual MC33926 (~$30)
  - 3A continuous, 5A peak
  - Better efficiency
  - Compact design

### For 6-Actuator System

**Recommended:**
- 2× TB6612FNG Dual Motor Driver (~$8 each)
  - 1.2A continuous per channel
  - Adequate for smaller actuators
  - More efficient than L298N

OR

- 6× BTS7960 43A High Power Driver (~$8 each)
  - Overkill but very reliable
  - Excellent for heavy-duty actuators

### H-Bridge Specifications Needed:
- Continuous current: 2-3A per actuator
- Peak current: 5A per actuator
- Operating voltage: 12V
- PWM frequency: 1-20 kHz
- Protection: Over-current, thermal

## 🔌 Power System

### Requirements

**Total Power Budget:**

| Component | Current Draw | Notes |
|-----------|-------------|-------|
| 3 Actuators (simultaneous) | 9-15A | Peak operation |
| 6 Actuators (simultaneous) | 12-24A | Peak operation |
| ESP32 | 0.5A | Including peripherals |
| IMU | 0.015A | Negligible |
| **Total (3-actuator)** | **10-16A** | At 12V |
| **Total (6-actuator)** | **13-25A** | At 12V |

### Power Supply Options

**Option 1: Direct Vehicle Connection**
- Connect to vehicle 12V auxiliary/accessory
- Add 20A inline fuse
- Use heavy gauge wire (12 AWG minimum)
- Add LC filter for noise reduction

**Option 2: Separate Battery**
- 12V 20Ah LiFePO4 battery (~$100)
- Charged via vehicle alternator
- Isolated from vehicle electronics
- Better noise immunity

**Required Components:**
- 20A automotive fuse + holder
- 12 AWG wire (power distribution)
- Anderson PowerPole connectors
- 100µF capacitors (near each motor driver)
- Reverse polarity protection diode

## 🔩 Mechanical Components

### Mounting Hardware

**Base Mounts (per actuator):**
- Ball joint or clevis mount
- M10 or 3/8" mounting bolts
- Lock washers and nuts
- Rubber vibration dampeners

**Platform Mounts:**
- Rotating ball joints (allow angular freedom)
- Stainless steel for weather resistance
- Load-rated for safety factor of 3×

### Structural Considerations

**For Tripod Configuration:**
- Mounting points form equilateral or isosceles triangle
- Base width ~60-80% of platform width
- Actuators at 30-45° when level

**For Stewart Platform:**
- Hexagonal base pattern
- Base radius: ~300-400mm
- Platform radius: ~240-320mm (0.8× base)
- Actuators at 30-50° when level

## 📡 Wiring & Connectors

### Signal Wiring (Low Voltage)
- 22-24 AWG stranded wire
- Shielded cable for I²C (IMU ↔ ESP32)
- Color coding:
  - Red: +3.3V
  - Black: GND
  - Yellow: I²C SDA
  - Green: I²C SCL
  - Blue: Position feedback

### Power Wiring (High Current)
- 12 AWG for main 12V distribution
- 14-16 AWG for individual actuators
- Anderson PowerPole for main connections
- Automotive blade connectors for switches

### Connectors
- Weatherproof connectors (IP67+) for external wiring
- DuPont connectors for ESP32 pins
- Spade terminals for motor drivers
- Heat shrink tubing for all connections

## 🛡️ Safety Components

### Limit Switches (Per Actuator)
- Mechanical microswitch (SPDT)
- Normally closed configuration
- Rated for 5A @ 12V
- Weatherproof housing
- Mounting brackets

### Additional Safety:
- Emergency stop button (latching)
- Status LEDs (power, active, fault)
- Fuses (one per actuator circuit)
- TVS diodes (voltage spike protection)
- Thermal protection (motor drivers)

## 💰 Cost Breakdown

### 3-Actuator System (Mid-Range)

| Component | Quantity | Unit Price | Total |
|-----------|----------|-----------|-------|
| Progressive Automations PA-14 | 3 | $150 | $450 |
| ESP32 DevKit | 1 | $12 | $12 |
| BNO055 Module | 1 | $35 | $35 |
| L298N H-Bridge | 3 | $5 | $15 |
| Power supply/wiring | 1 | $50 | $50 |
| Mounting hardware | 1 | $100 | $100 |
| Limit switches | 6 | $3 | $18 |
| Connectors/misc | 1 | $50 | $50 |
| **TOTAL** | | | **~$730** |

### 6-Actuator System (Stewart)

| Component | Quantity | Unit Price | Total |
|-----------|----------|-----------|-------|
| Mid-range actuators | 6 | $120 | $720 |
| ESP32 DevKit | 1 | $12 | $12 |
| BNO055 Module | 1 | $35 | $35 |
| TB6612FNG drivers | 6 | $8 | $48 |
| Power supply/wiring | 1 | $75 | $75 |
| Mounting hardware | 1 | $150 | $150 |
| Limit switches | 12 | $3 | $36 |
| Connectors/misc | 1 | $75 | $75 |
| **TOTAL** | | | **~$1,151** |

*Prices are approximate and may vary by supplier*

## 🛒 Recommended Suppliers

### Electronics:
- **Adafruit** (IMU, sensors, cables)
- **SparkFun** (sensors, ESP32 modules)
- **Amazon** (motor drivers, basic components)
- **DigiKey/Mouser** (precision components)

### Actuators:
- **Progressive Automations** (direct)
- **Firgelli** (direct)
- **Actuonix** (direct or Amazon)
- **Servo City** (mounting hardware)

### Hardware:
- **McMaster-Carr** (mechanical parts)
- **Bolt Depot** (fasteners)
- **Amazon** (basic hardware)

## 📋 Tool Requirements

### For Assembly:
- Soldering iron + solder
- Wire strippers/crimpers
- Multimeter
- Drill + bits
- Hex key set
- Screwdrivers
- Heat gun (for heat shrink)

### For Calibration:
- Digital level or smartphone level app
- Tape measure
- Markers/tape for alignment

## 🔧 Testing Equipment

### Recommended (Optional):
- Oscilloscope (for debugging PWM signals)
- Bench power supply (for initial testing)
- Current meter (for power monitoring)
- Logic analyzer (for I²C debugging)

## 📝 Additional Notes

### Weather Protection:
- Use conformal coating on PCBs
- Silicone grease on connectors
- Weather-resistant enclosures for electronics
- Cable glands for wire entry points

### Vibration Resistance:
- Loctite on all mechanical fasteners
- Vibration-dampening mounts for ESP32
- Strain relief on all cables

### Serviceability:
- Label all wires
- Use color-coded cables
- Keep schematic in waterproof sleeve
- Design for easy actuator replacement

## 🎯 MVP Recommendations

**For Testing (Lowest Cost):**
- 3× Actuonix L16 actuators
- L298N motor drivers
- MPU-6050 IMU
- **Total: ~$300-400**

**For Production (Recommended):**
- 3× Progressive Automations PA-14
- L298N or TB6612 drivers
- BNO055 IMU
- Proper weatherproofing
- **Total: ~$700-800**

**For Premium (Best Performance):**
- 6× Firgelli FA-PO actuators (Stewart)
- BTS7960 drivers
- BNO055 IMU
- Custom PCB for clean installation
- **Total: ~$1,500-2,000**
