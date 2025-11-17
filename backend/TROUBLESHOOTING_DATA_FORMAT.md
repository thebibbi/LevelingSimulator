# 🔧 Troubleshooting: Data Format Issue

## What's Happening

Sensor Logger is sending data, but it's wrapped in a format we need to decode. The app sends:
```json
{
  "messageId": "...",
  "sessionId": "...", 
  "deviceId": "...",
  "payload": { ... actual sensor data here ... }
}
```

We need to look inside the `payload` to find the accelerometer data.

---

## 🔍 **Step 1: Run the Inspector Tool**

Let's see EXACTLY what Sensor Logger is sending:

```bash
python sensor_logger_inspector.py
```

This will:
1. Start an HTTP server on port 8080
2. Print every message it receives in full detail
3. Show you the structure of the data

---

## 📱 **Step 2: Record a Few Messages**

1. Keep the same settings in Sensor Logger:
   - URL: `http://YOUR_IP:8080/imu`
   - Format: JSON
   - Method: POST

2. **Tap RECORD** (red button)

3. **Watch your computer terminal** - you'll see the full JSON structure printed out

4. After 5 messages, it will give you an analysis

---

## 📋 **Step 3: Look for These Fields**

When you see the output, look for:

### **Accelerometer data** - could be named:
- `accelerometer`
- `accel`
- `acceleration`
- `Accelerometer`
- `acc`

### **Format** - could be:
```json
// Option A: Simple dict
"accelerometer": {
  "x": 0.12,
  "y": -0.05,
  "z": 9.81
}

// Option B: Array
"accelerometer": [0.12, -0.05, 9.81]

// Option C: Nested with timestamp
"accelerometer": [
  {"x": 0.12, "y": -0.05, "z": 9.81, "time": 1234567890}
]

// Option D: Multiple readings
"accelerometer": [
  [0.12, -0.05, 9.81],
  [0.13, -0.04, 9.82]
]
```

---

## 💬 **Step 4: Copy the Output and Tell Me**

Once you run the inspector and see a few messages, **copy the output** from your terminal and share:

1. What's inside the `payload` field?
2. What are the field names?
3. Is the data in arrays or dictionaries?

Example of what to share:
```
The payload looks like this:
{
  "payload": {
    "accelerometerAccelerationX": 0.123,
    "accelerometerAccelerationY": -0.456,
    "accelerometerAccelerationZ": 9.789,
    "gyroRotationX": 0.01,
    ...
  }
}
```

Then I can update the code to parse it correctly!

---

## 🚀 **Quick Fix (If You See the Data Structure)**

If you can see the accelerometer data in the inspector output, you can tell me:

**"The accelerometer values are at:"**
- `payload.accelerometer.x/y/z`
- `payload.accelX/accelY/accelZ`
- `payload[0].x/y/z`
- Or whatever the actual path is

And I'll fix the code immediately!

---

## 🎯 **Alternative: Common Sensor Logger Formats**

While the inspector runs, here are some common formats I can try:

### **Format 1: Standard iOS Motion**
```json
{
  "payload": {
    "accelerometerAccelerationX": 0.1,
    "accelerometerAccelerationY": -0.2,
    "accelerometerAccelerationZ": 9.8
  }
}
```

### **Format 2: Simplified**
```json
{
  "payload": {
    "accelX": 0.1,
    "accelY": -0.2,
    "accelZ": 9.8
  }
}
```

### **Format 3: Nested Object**
```json
{
  "payload": {
    "motion": {
      "acceleration": {
        "x": 0.1,
        "y": -0.2,
        "z": 9.8
      }
    }
  }
}
```

Let me know which one matches what you see!

---

## ⚡ **Updated Code Ready**

I've already updated `imu_streamer_http.py` to:
1. Look inside the `payload` field first
2. Handle multiple data formats
3. Print debug info on the first message
4. Show helpful error messages

**Try running the visualizer again:**
```bash
python platform_visualizer_http.py tripod
```

Now when you record, it will:
- Print the FIRST message in full
- Show what keys it found
- Try to extract the data

---

## 🐛 **If Still Not Working**

Run the inspector, then copy and paste the output here. I'll see exactly what format Sensor Logger is using and update the code to match it perfectly!

```bash
python sensor_logger_inspector.py
# Then start recording and copy the terminal output
```

---

## 📝 **Files Updated**

- **[imu_streamer_http.py](computer:///mnt/user-data/outputs/imu_streamer_http.py)** - Now handles payload wrapper
- **[sensor_logger_inspector.py](computer:///mnt/user-data/outputs/sensor_logger_inspector.py)** - NEW diagnostic tool

Both in your outputs folder!
