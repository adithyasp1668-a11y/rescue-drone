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

2️⃣ AI Does Not Directly Control the Motors

The system uses a layered architecture:

AI Perception
      ↓
Sensor Fusion
      ↓
Navigation Decision
      ↓
Pixhawk
      ↓
Flight Stabilization
      ↓
Motors

The Raspberry Pi performs high-level intelligence and decision-making, while Pixhawk handles the low-level flight-control and stabilization layer.

3️⃣ Autonomous Search Instead of Random Movement

The drone follows a structured search strategy:

100 m × 100 m Search Area
        +
5 m Lane Spacing
        ↓
Zig-Zag / Lawn-Mower Search

The navigation controller maintains:

Lane
Phase
Action
Direction
X Position
Y Position
Search Progress

This gives the rescue mission a defined search strategy instead of depending entirely on manual piloting.

4️⃣ Mission-Aware Obstacle Avoidance

A key part of the design is that obstacle avoidance does not simply stop the mission permanently.

The logic is:

Current Mission
      ↓
Obstacle Detected
      ↓
Save Previous Navigation State
      ↓
Perform Avoidance
      ↓
Obstacle Cleared
      ↓
Restore Previous State
      ↓
Continue Mission

For example:

FORWARD
   ↓
OBSTACLE
   ↓
AVOID
   ↓
CLEAR
   ↓
FORWARD

The same concept can be applied while the system is searching or tracking a detected target.

5️⃣ Edge AI

The major AI processing is performed locally on the Raspberry Pi.

Camera
  ↓
YOLO11n

Microphones
  ↓
Vosk

Sensor Data
  ↓
AI Fusion

This reduces dependence on cloud processing and allows the prototype to perform its core perception and decision-making locally.

6️⃣ Real-Time Explainable Decision Making

The system does not only generate a movement command.

It also exposes why the command was generated.

Example:

HELP                : YES
Audio Confidence    : 93%
Person              : YES
YOLO Confidence     : 87%
Fusion Confidence   : 90%
Direction           : LEFT
Person Status       : CONFIRMED
Command             : MOVE_LEFT

This information is displayed through the real-time dashboard.

The operator can therefore observe the complete chain:

Sensor Data
    ↓
AI Detection
    ↓
Confidence
    ↓
Decision
    ↓
Navigation Command
# ⭐ Why Our Prototype Stands Out

This project is not designed as a simple camera-based drone or a manually controlled UAV.

Our approach combines **multimodal AI, autonomous search, mission-aware obstacle avoidance, and flight-controller integration** into one system.

🔬 From Detection to Action

The important part of the project is not just detecting a person.

The complete pipeline is:

                    DETECT
                       │
                       ▼
             ┌─────────────────┐
             │ Camera + Audio  │
             └────────┬────────┘
                      │
                      ▼
                 AI FUSION
                      │
                      ▼
              CONFIDENCE CHECK
                      │
                      ▼
              TARGET DECISION
                      │
                      ▼
                DIRECTION
                      │
                      ▼
             NAVIGATION DECISION
                      │
             ┌────────┼────────┐
             ▼        ▼        ▼
           SEARCH   TRACK     AVOID
             │        │        │
             └────────┼────────┘
                      ▼
                   PIXHAWK
                      │
                      ▼
               FLIGHT CONTROL

🚀 Prototype Maturity

The project has been developed as a modular hardware-software prototype rather than a software-only simulation.

The implemented system brings together:

Raspberry Pi 4
      +
ESP32
      +
Camera
      +
2 × INMP441
      +
Ultrasonic Sensor
      +
YOLO11n
      +
Vosk
      +
Navigation Controller
      +
Pixhawk
      +
Flask Dashboard

This allows the individual perception, navigation, safety and monitoring components to be demonstrated as one integrated system.

🎯 The Core Innovation

A multimodal Edge-AI rescue drone that combines visual person detection, emergency audio detection, directional sensing, autonomous area search, mission-aware obstacle avoidance and Pixhawk-based flight control in a single integrated architecture.
