import json
import os
import tempfile
import time


BASE_DIR = "/home/pii/rescue_drone/ai"

AI_FILE = os.path.join(BASE_DIR, "telemetry.json")
MOTOR_FILE = os.path.join(BASE_DIR, "motor_telemetry.json")


def _write_json(filename, data):
    """
    Atomic JSON write.
    Dashboard will never read half-written JSON.
    """

    directory = os.path.dirname(filename)

    fd, temp_file = tempfile.mkstemp(
        dir=directory,
        prefix=".telemetry_",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)

        os.replace(temp_file, filename)

    except Exception:
        try:
            os.unlink(temp_file)
        except Exception:
            pass


def update_ai(
    help_detected=False,
    audio_confidence=0.0,
    camera_person=False,
    camera_confidence=0.0,
    distance_cm=None,
    path="UNKNOWN",
    fused_confidence=0.0,
    direction="UNKNOWN",
    command="STOP",
    person_status="UNKNOWN"
):

    data = {
        "timestamp": time.time(),

        "audio": {
            "help": bool(help_detected),
            "confidence": float(audio_confidence)
        },

        "camera": {
            "person": bool(camera_person),
            "confidence": float(camera_confidence)
        },

        "ultrasonic": {
            "distance_cm":
                None if distance_cm is None
                else float(distance_cm),

            "path": str(path)
        },

        "fusion": {
            "person_confidence": float(fused_confidence),
            "direction": str(direction or "UNKNOWN"),
            "command": str(command or "STOP"),
            "person_status": str(person_status)
        }
    }

    _write_json(AI_FILE, data)


def update_motors(
    command="STOP",
    angle=0,
    m1=0,
    m2=0,
    m3=0,
    m4=0
):

    data = {
        "timestamp": time.time(),

        "command": str(command),

        "angle": float(angle),

        "motors": {
            "M1": float(m1),
            "M2": float(m2),
            "M3": float(m3),
            "M4": float(m4)
        }
    }

    _write_json(MOTOR_FILE, data)
