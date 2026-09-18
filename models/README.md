# AI Models

This project uses two AI models for autonomous rescue detection.

## 1. YOLO11n

**YOLO11n** is used for real-time person detection from the Raspberry Pi camera.

### Purpose

- Detect people in the camera frame
- Calculate person detection confidence
- Provide visual information for AI sensor fusion
- Support victim detection during autonomous search

### Model Format


YOLO11n ONNX

 2.vosk

**Vosk**  is used for offline speech recognition from the two INMP441 microphones.

###Purpose

-Detect emergency speech
-Identify the HELP command
-Process audio locally on the Raspberry Pi
-Provide audio information for AI sensor fusion
