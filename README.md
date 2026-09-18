# 🚁 AI-Powered Autonomous Rescue Drone

### Edge AI • Computer Vision • Audio Intelligence • Sensor Fusion • Autonomous Navigation • Obstacle Avoidance • Pixhawk • Real-Time Monitoring

An AI-powered autonomous rescue drone prototype designed to assist search-and-rescue operations by systematically searching an area, detecting possible victims using **computer vision and emergency audio detection**, estimating the direction of a detected victim, identifying obstacles, performing autonomous navigation, and providing real-time system monitoring.

The system combines:

- Artificial Intelligence
- Computer Vision
- Speech Recognition
- Directional Audio Processing
- Sensor Fusion
- Autonomous Navigation
- Obstacle Avoidance
- Embedded Systems
- UAV Flight Control
- Real-Time Monitoring

---

# 🎯 Problem Statement

> **A deployable AI-powered autonomous drone that aids search-and-rescue operations by detecting people and hazards, thereby improving responder safety and reducing victim discovery time.**

---

# 💡 Proposed Solution

We propose an **AI-powered autonomous rescue drone** that combines visual, audio and environmental sensing with autonomous navigation.

The drone uses a:

- **Raspberry Pi 4** as the Edge-AI and system-computing platform
- **ESP32** for sensor acquisition
- **Raspberry Pi Camera** for visual perception
- **YOLO11n** for person detection
- **Two INMP441 microphones** for directional audio sensing
- **Vosk** for offline speech recognition and HELP detection
- **Ultrasonic sensor** for obstacle detection
- **Navigation Controller** for autonomous search and mission logic
- **Pixhawk** for flight-control and stabilization
- **Flask dashboard** for real-time monitoring

The central idea is to combine **what the camera sees** with **what the microphones hear**, while continuously checking the surrounding environment for obstacles.

---

# 🧠 Core Concept

The complete system follows:

```text
SENSE
  ↓
DETECT
  ↓
UNDERSTAND
  ↓
FUSE
  ↓
DECIDE
  ↓
NAVIGATE
  ↓
AVOID
  ↓
RECOVER
  ↓
MONITOR
  ↓
RESCUE

---

# ⭐ Why Our Prototype Stands Out

This project is not designed as a simple camera-based drone or a manually controlled UAV.

Our approach combines **multimodal AI, autonomous search, mission-aware obstacle avoidance, and flight-controller integration** into one system.

### 1️⃣ Multimodal Victim Detection

Instead of depending only on a camera, the system combines:

📷 Vision
   +
🎙 Audio
   +
🧭 Direction
   +
📡 Environmental Sensing
         ↓
       CAMERA
         ↓
      YOLO11n
         ↓
  Person Detection
   ↓
 Visual Confidence
        │
        │
        ├─────────────────┐
        │                 │
        ▼                 ▼
     AUDIO            DIRECTION
        │                 │
      Vosk          Left / Right
        │                 │
      HELP                │
        │                 │
        └────────┬────────┘
                 ▼
          🧠 AI FUSION
                 │
                 ▼
        Person Confidence
                 │
          ┌──────┴──────┐
          │             │
       LIKELY        CONFIRMED
          │             │
          └──────┬──────┘
                 ▼
        Navigation Decision
                 │
       ┌─────────┼──────────┐
       ▼         ▼          ▼
    SEARCH     TRACK      AVOID
       │         │          │
       └─────────┼──────────┘
                 ▼
              PIXHAWK
                 │
                 ▼
          Flight Control
                 │
                 ▼
              RESCUE

Example:
HELP                : YES
Audio Confidence    : 93%
Person              : YES
YOLO Confidence     : 87%
Fusion Confidence   : 90%
Direction           : LEFT
Person Status       : CONFIRMED
Navigation Command  : MOVE_LEFT

🚁 Mission-Level Intelligence

The prototype therefore operates at three levels:

LEVEL 1 — PERCEPTION
Camera + Audio + Ultrasonic
              ↓
LEVEL 2 — INTELLIGENCE
Detection + Fusion + Confidence
              ↓
LEVEL 3 — AUTONOMY
Search + Tracking + Avoidance + Navigation
              ↓
          PIXHAWK
              ↓
       FLIGHT CONTROL
