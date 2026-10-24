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


# 🎯 Problem Statement

> **A deployable AI-powered autonomous drone that aids search-and-rescue operations by detecting people and hazards, thereby improving responder safety and reducing victim discovery time.**


# 💡 Proposed Solution

We propose an **AI-powered autonomous rescue drone** that combines visual, audio and environmental sensing with autonomous navigation.

The drone uses a:

- **Raspberry Pi 4** as the Edge-AI and system-computing platform
- **ESP32** for sensor acquisition
- RPLIDAR A1M8** for Obstacle detection 
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
📡 Environmental Sensing(obstacle detection)

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

This separation makes the system modular, safer to develop, and easier to extend.

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
A1M8 RPLIDAR
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

## 🛰️ LiDAR Integration and GPS-Aware SLAM Navigation

The rescue drone integrates the **RPLIDAR A1M8** with its onboard navigation system to improve environmental awareness and support navigation in GPS-denied environments.

### 1. RPLIDAR A1M8 Integration

The RPLIDAR A1M8 provides 2D laser-scan measurements of the surrounding environment. These measurements support obstacle detection and provide scan data for SLAM-based mapping.

Key functions:
- Capture surrounding distance measurements using LiDAR.
- Detect obstacles using LiDAR scan data.
- Publish or process scan measurements for navigation, according to the configured software pipeline.
- Support environmental mapping in GPS-denied areas.

### 2. Automatic GPS and SLAM Navigation Selection

The system is designed to select its navigation mode based on GPS availability.

| Operating condition | Navigation mode |
|---|---|
| Valid GPS fix available | GPS-based navigation |
| GPS unavailable or GPS-denied environment | SLAM-based navigation |

**GPS-based mode:** The drone uses available GPS information for navigation and follows its configured search strategy.

**SLAM-based mode:** When GPS is unavailable, the SLAM navigation pipeline uses LiDAR scan data to estimate the surrounding environment and support navigation without relying on GPS coordinates.

The mode-selection logic coordinates the navigation system so that the appropriate navigation controller is active for the selected mode.

> GPS availability should be determined using a valid GPS fix, not simply whether a GPS device is connected. Switching between navigation modes must account for localization readiness and safe controller handover.

### 3. LiDAR Obstacle Detection and Navigation

The LiDAR obstacle-monitoring component analyses scan measurements to identify obstacles around the drone.

Conceptual processing flow:

1. Acquire LiDAR scan data.
2. Analyse obstacle distances and directions.
3. Determine whether the navigation path is clear or obstructed.
4. Provide obstacle information to the navigation logic.
5. Support avoidance decisions and mission continuation when the path becomes clear.

### 4. GPS-Denied Search and Rescue

GPS signals may be unavailable or unreliable inside caves, tunnels, enclosed structures, and certain disaster environments.

In these situations, LiDAR-based SLAM can help the drone build a map of its surroundings while estimating its position relative to that map. With the configured ROS 2 and `slam_toolbox` pipeline, scan data can support mapping and navigation without depending on GPS positioning.

SLAM does not automatically guarantee safe flight. Reliable operation also depends on scan quality, localization, controller coordination, flight stabilization, and testing in the intended environment.

### 5. Updated Navigation Architecture

```text
                 GPS STATUS
                     |
           +---------+---------+
           |                   |
      Valid GPS Fix       GPS Unavailable
           |                   |
     GPS Navigation       SLAM Navigation
                               |
                       RPLIDAR A1M8
                               |
                         Laser Scans
                               |
                       SLAM / Mapping
                               |
                    Obstacle-Aware Decisions
           |                   |
           +---------+---------+
                     |
              Navigation Logic
                     |
                   Pixhawk
                     |
             Flight Controller
                     |
                   Motors
```

