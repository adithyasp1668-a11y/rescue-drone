# Documentation

This directory contains supporting documentation and system diagrams for the AI-Powered Autonomous Rescue Drone.

The documentation is intended to help users, developers and evaluators understand the system architecture, hardware setup, AI pipeline and autonomous navigation.

## Planned Documentation

### 1. System Architecture

Shows the relationship between:

- Raspberry Pi 4
- ESP32
- Pixhawk
- Camera
- INMP441 microphones
- Ultrasonic sensor
- AI processing
- Navigation controller
- Flight-control system

### 2. System Flow

Shows the complete processing pipeline:


Sensors
   ↓
AI Perception
   ↓
Person / HELP Detection
   ↓
Sensor Fusion
   ↓
Navigation Decision
   ↓
Obstacle Avoidance / Target Tracking
   ↓
Pixhawk
   ↓
Flight Control
