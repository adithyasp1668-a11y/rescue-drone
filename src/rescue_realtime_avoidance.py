import os
import sys
import json
import time
import struct
import threading
import queue
from collections import deque
from difflib import SequenceMatcher

import serial
import numpy as np
import cv2
import onnxruntime as ort
from picamera2 import Picamera2
from vosk import Model, KaldiRecognizer
from pixhawk_controller import PixhawkController
from telemetry import update_ai
# ============================================================
# RESCUE DRONE - REAL-TIME SENSOR FUSION
# ============================================================

PORT = "/dev/ttyUSB0"
BAUD = 921600

SAMPLE_RATE = 16000
CHANNELS = 2
SAMPLE_WIDTH = 2

BASE_DIR = "/home/pii/rescue_drone/ai"

VOSK_MODEL = f"{BASE_DIR}/speech_model/model"
YOLO_MODEL = f"{BASE_DIR}/yolo11n.onnx"

latest_camera_frame = None
camera_frame_lock = threading.Lock()
# ============================================================
# ULTRASONIC SAFETY
# ============================================================

SAFETY_DISTANCE_CM = 100.0
EMERGENCY_STOP_CM = 40.0


# ============================================================
# HELP EVENT LOCK
# ============================================================

EVENT_LOCK_SECONDS = 20.0


# ============================================================
# AUDIO / VAD
# ============================================================

CALIBRATION_SECONDS = 2.0

ONSET_CONFIRM_CHUNKS = 2

# Increased so short HELP is not cut off too aggressively
SPEECH_END_CHUNKS = 12

# IMPORTANT:
# Your previous 0.24 / 0.30 second HELP recordings
# were being rejected by 0.35 seconds.
MIN_SPEECH_SECONDS = 0.15

MAX_SPEECH_SECONDS = 8.0

# Keep some audio before speech starts
PRE_ROLL_SECONDS = 0.25


# ============================================================
# MICROPHONE DIRECTION
# ============================================================

DIRECTION_TIME_THRESHOLD = 0.08
DIRECTION_ENERGY_RATIO = 1.20


# ============================================================
# AUDIO CONFIDENCE
# ============================================================

AUDIO_HELP_THRESHOLD = 0.65


# ============================================================
# YOLO
# ============================================================

YOLO_THRESHOLD = 0.25
YOLO_NMS = 0.45

CAMERA_INTERVAL = 0.8


# ============================================================
# ESP32 PACKET HEADERS
# ============================================================

AUDIO_H1 = 0xAA
AUDIO_H2 = 0x55

DIST_H1 = 0x55
DIST_H2 = 0xAA


# ============================================================
# HELP PHRASES
# ============================================================

HELP_PHRASES = [
    "help",
    "help me",
    "save me",
    "someone help me",
    "please help me",
    "i need help",
    "somebody help me",
]


# ============================================================
# GLOBAL STATE
# ============================================================

running = True

ser = None

audio_queue = queue.Queue(maxsize=100)


# -----------------------------
# Ultrasonic state
# -----------------------------

distance_lock = threading.Lock()

latest_distance = None
latest_distance_time = 0.0


# -----------------------------
# Camera state
# -----------------------------

camera_lock = threading.Lock()

person_detected = False
person_confidence = 0.0


# -----------------------------
# Rescue lock
# -----------------------------

rescue_lock = threading.Lock()

rescue_locked_until = 0.0


# -----------------------------
# Hardware
# -----------------------------

picam2 = None

yolo_session = None
yolo_input_name = None

vosk_model = None


# ============================================================
# BASIC HELPERS
# ============================================================

def rms(samples):

    if len(samples) == 0:
        return 0.0

    x = np.asarray(
        samples,
        dtype=np.float32
    )

    return float(
        np.sqrt(
            np.mean(x * x)
        )
    )


def clamp(value):

    return max(
        0.0,
        min(
            1.0,
            float(value)
        )
    )


def clean_text(text):

    text = text.lower()

    text = "".join(
        c
        if c.isalnum() or c == " "
        else " "
        for c in text
    )

    return " ".join(
        text.split()
    )


# ============================================================
# HELP DETECTION
# ============================================================

def help_score(text):

    text = clean_text(text)

    if not text:
        return 0.0

    words = text.split()

    # Exact known phrases
    if text in HELP_PHRASES:
        return 1.0

    # HELP word detected
    if "help" in words:

        if "me" in words:
            return 0.90

        return 0.82

    # Fuzzy matching for small Vosk recognition errors
    best = 0.0

    for phrase in HELP_PHRASES:

        score = SequenceMatcher(
            None,
            text,
            phrase
        ).ratio()

        best = max(
            best,
            score
        )

    if best >= 0.82:
        return best

    return 0.0


# ============================================================
# VOSK RECOGNITION
# ============================================================

def vosk_result(audio_bytes):

    recognizer = KaldiRecognizer(
        vosk_model,
        SAMPLE_RATE
    )

    recognizer.SetWords(True)

    chunk_size = 4000

    for i in range(
        0,
        len(audio_bytes),
        chunk_size
    ):

        recognizer.AcceptWaveform(
            audio_bytes[
                i:i + chunk_size
            ]
        )

    try:

        result = json.loads(
            recognizer.FinalResult()
        )

    except Exception:

        result = {}

    text = clean_text(
        result.get(
            "text",
            ""
        )
    )

    words = result.get(
        "result",
        []
    )

    all_confidences = []

    for word in words:

        try:

            all_confidences.append(
                float(
                    word["conf"]
                )
            )

        except Exception:
            pass


    # Specifically look at the confidence
    # of the word HELP.
    help_confidences = []

    for word in words:

        try:

            word_text = clean_text(
                word.get(
                    "word",
                    ""
                )
            )

            if (
                word_text == "help"
                and
                "conf" in word
            ):

                help_confidences.append(
                    float(
                        word["conf"]
                    )
                )

        except Exception:
            pass


    if help_confidences:

        vosk_confidence = max(
            help_confidences
        )

    elif all_confidences:

        vosk_confidence = float(
            np.mean(
                all_confidences
            )
        )

    else:

        vosk_confidence = 0.0


    match = help_score(
        text
    )


    if (
        match > 0
        and
        vosk_confidence > 0
    ):

        confidence = (
            0.65 * vosk_confidence
            +
            0.35 * match
        )

    elif match > 0:

        confidence = match

    else:

        confidence = 0.0


    return (
        text,
        clamp(confidence),
        match
    )


# ============================================================
# SERIAL READER
# ============================================================

def read_exact(count):

    data = bytearray()

    while (
        running
        and
        len(data) < count
    ):

        chunk = ser.read(
            count - len(data)
        )

        if not chunk:
            return None

        data.extend(
            chunk
        )

    return bytes(data)


def serial_reader():

    global latest_distance
    global latest_distance_time

    while running:

        try:

            byte1 = ser.read(1)

            if not byte1:
                continue


            byte2 = ser.read(1)

            if not byte2:
                continue


            first = byte1[0]
            second = byte2[0]


            # =================================================
            # ULTRASONIC PACKET
            # =================================================

            if (
                first == DIST_H1
                and
                second == DIST_H2
            ):

                raw = read_exact(4)

                if raw:

                    distance = struct.unpack(
                        "<f",
                        raw
                    )[0]

                    if (
                        np.isfinite(distance)
                        and
                        distance >= 0
                    ):

                        with distance_lock:

                            latest_distance = float(
                                distance
                            )

                            latest_distance_time = (
                                time.time()
                            )


            # =================================================
            # AUDIO PACKET
            # =================================================

            elif (
                first == AUDIO_H1
                and
                second == AUDIO_H2
            ):

                frame_bytes = read_exact(2)

                if not frame_bytes:
                    continue


                frames = struct.unpack(
                    "<H",
                    frame_bytes
                )[0]


                if (
                    frames <= 0
                    or
                    frames > 1000
                ):

                    continue


                raw_audio = read_exact(
                    frames * 4
                )

                if not raw_audio:
                    continue


                try:

                    samples = np.frombuffer(
                        raw_audio,
                        dtype="<i2"
                    ).reshape(
                        frames,
                        2
                    )

                except Exception:

                    continue


                try:

                    audio_queue.put_nowait(
                        samples.copy()
                    )

                except queue.Full:

                    try:
                        audio_queue.get_nowait()
                    except queue.Empty:
                        pass

                    try:

                        audio_queue.put_nowait(
                            samples.copy()
                        )

                    except queue.Full:
                        pass


        except Exception as error:

            if running:

                print(
                    "Serial reader error:",
                    error
                )

                time.sleep(
                    0.1
                )


def get_distance():

    with distance_lock:

        return latest_distance


# ============================================================
# YOLO NMS
# ============================================================

def yolo_nms(
    boxes,
    scores
):

    if not boxes:
        return []


    indices = cv2.dnn.NMSBoxes(
        boxes,
        scores,
        YOLO_THRESHOLD,
        YOLO_NMS
    )


    if indices is None:
        return []


    return np.asarray(
        indices
    ).reshape(
        -1
    ).tolist()


# ============================================================
# YOLO PERSON DETECTION
# ============================================================

def yolo_person(frame):

    original_height, original_width = (
        frame.shape[:2]
    )


    image = cv2.resize(
        frame,
        (
            640,
            640
        )
    )


    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )


    image = image.astype(
        np.float32
    ) / 255.0


    image = np.transpose(
        image,
        (
            2,
            0,
            1
        )
    )


    image = np.expand_dims(
        image,
        axis=0
    )


    outputs = yolo_session.run(
        None,
        {
            yolo_input_name:
            image
        }
    )


    output = outputs[0]

    predictions = output[0]


    # YOLO output:
    #
    # (84, 8400)
    #
    # Convert to:
    #
    # (8400, 84)

    if (
        predictions.shape[0]
        <
        predictions.shape[1]
    ):

        predictions = predictions.T


    boxes = []
    scores = []
    raw_results = []


    x_scale = (
        original_width
        /
        640.0
    )

    y_scale = (
        original_height
        /
        640.0
    )


    for row in predictions:

        if len(row) < 84:
            continue


        class_scores = row[4:]


        class_id = int(
            np.argmax(
                class_scores
            )
        )


        confidence = float(
            class_scores[
                class_id
            ]
        )


        # COCO class 0 = person

        if class_id != 0:
            continue


        if confidence < YOLO_THRESHOLD:
            continue


        center_x = row[0]
        center_y = row[1]

        width = row[2]
        height = row[3]


        x = int(
            (
                center_x
                -
                width / 2
            )
            *
            x_scale
        )


        y = int(
            (
                center_y
                -
                height / 2
            )
            *
            y_scale
        )


        box_width = max(
            1,
            int(
                width
                *
                x_scale
            )
        )


        box_height = max(
            1,
            int(
                height
                *
                y_scale
            )
        )


        x = max(
            0,
            x
        )

        y = max(
            0,
            y
        )


        boxes.append(
            [
                x,
                y,
                box_width,
                box_height
            ]
        )


        scores.append(
            confidence
        )


        raw_results.append(
            (
                confidence,
                x,
                y,
                box_width,
                box_height
            )
        )


    keep = yolo_nms(
        boxes,
        scores
    )


    if not keep:

        return (
            False,
            0.0
        )


    best = max(
        (
            raw_results[i]
            for i in keep
        ),
        key=lambda item: item[0]
    )


    confidence = best[0]


    return (
        True,
        clamp(
            confidence
        )
    )


# ============================================================
# CAMERA LOOP
# ============================================================

def camera_loop():

    global person_detected
    global person_confidence


    while running:

        try:

            frame = (
                picam2.capture_array()
            )
            global latest_camera_frame
            with camera_frame_lock:
                latest_camera_frame = frame.copy()

            frame_bgr = cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2BGR
            )
            try:
                cv2.imwrite(
                    "/home/pii/rescue_drone/ai/latest_camera.jpg",
                    frame_bgr,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        75
                    ]
                )
            except Exception as camera_save_error:
                print(
                    "camera stream save error:",
                    camera_save_error
                ) 

            detected, confidence = (
                yolo_person(
                    frame_bgr
                )
            )


            with camera_lock:

                person_detected = (
                    detected
                )

                person_confidence = (
                    confidence
                )


        except Exception as error:

            if running:

                print(
                    "Camera error:",
                    error
                )


        time.sleep(
            CAMERA_INTERVAL
        )


def get_camera():

    with camera_lock:

        return (
            person_detected,
            person_confidence
        )


# ============================================================
# MICROPHONE DIRECTION
# ============================================================

def direction_from_mics(
    left_onset,
    right_onset,
    left_peak,
    right_peak
):

    if (
        left_onset is None
        and
        right_onset is None
    ):

        return None


    if (
        left_onset is not None
        and
        right_onset is None
    ):

        return "LEFT"


    if (
        right_onset is not None
        and
        left_onset is None
    ):

        return "RIGHT"


    time_difference = abs(
        left_onset
        -
        right_onset
    )


    print(
        "Microphone onset difference:",
        f"{time_difference * 1000:.1f} ms"
    )


    print(
        "LEFT peak energy :",
        f"{left_peak:.1f}"
    )


    print(
        "RIGHT peak energy:",
        f"{right_peak:.1f}"
    )


    # Strong timing difference

    if (
        time_difference
        >=
        DIRECTION_TIME_THRESHOLD
    ):

        if (
            left_onset
            <
            right_onset
        ):

            return "LEFT"

        return "RIGHT"


    # Timing almost identical.
    # Use microphone energy.

    if (
        left_peak
        >
        right_peak
        *
        DIRECTION_ENERGY_RATIO
    ):

        return "LEFT"


    if (
        right_peak
        >
        left_peak
        *
        DIRECTION_ENERGY_RATIO
    ):

        return "RIGHT"


    return None


# ============================================================
# SENSOR FUSION
# ============================================================

def fused_person_confidence(
    audio_confidence,
    camera_person,
    camera_confidence
):

    if not camera_person:

        # Audio alone is NOT proof of a person.
        return clamp(
            audio_confidence
            *
            0.55
        )


    # Geometric mean:
    #
    # 92% audio + 87% camera
    # gives approximately 89.5%
    #
    # sqrt(0.92 * 0.87) = 0.895

    return clamp(
        np.sqrt(
            audio_confidence
            *
            camera_confidence
        )
    )


# ============================================================
# COMMAND DECISION
# ============================================================

def command_for(
    direction,
    distance
):

    # STOP always has highest priority.

    if distance is None:

        return "STOP"


    # Emergency obstacle

    if (
        distance
        <=
        EMERGENCY_STOP_CM
    ):

        return "STOP"


    # Safety obstacle

    if (
        distance
        <
        SAFETY_DISTANCE_CM
    ):

        return "STOP"


    # Path clear

    if direction == "LEFT":

        return "MOVE_LEFT"


    if direction == "RIGHT":

        return "MOVE_RIGHT"


    return "STOP"


# ============================================================
# PRINT FUSION RESULT
# ============================================================

def print_fusion(
    audio_confidence,
    direction
):

    distance = get_distance()

    camera_person, camera_confidence = (
        get_camera()
    )


    fused_confidence = (
        fused_person_confidence(
            audio_confidence,
            camera_person,
            camera_confidence
        )
    )


    command = command_for(
        direction,
        distance
    )

    update_ai(
        help_detected=(audio_confidence >= 0.60),
        audio_confidence=audio_confidence,
        camera_person=camera_person,
        camera_confidence=camera_confidence,
        distance_cm=distance,
        path=(
            "CLEAR"
            if distance is not None
            and distance > SAFETY_DISTANCE_CM
            else "OBSTACLE"
        ),
        fused_confidence=fused_confidence,
        direction=direction if direction else "UNKNOWN",
        command=command,
        person_status=(
            "CONFIRMED"
            if camera_person and fused_confidence >= 0.80
            else "LIKELY"
            if camera_person and fused_confidence >= 0.60
            else "POSSIBLE"
            if camera_person
            else "AUDIO ALERT / VISUAL NOT CONFIRMED"
        )
    )
    print()
    print("--------------------------------")
    print("AUDIO")
    print("--------------------------------")

    print(
        "HELP             : YES"
    )

    print(
        "Audio confidence :",
        f"{audio_confidence * 100:.1f}%"
    )


    print()
    print("--------------------------------")
    print("CAMERA")
    print("--------------------------------")

    print(
        "Person           :",
        "YES"
        if camera_person
        else
        "NO"
    )

    print(
        "YOLO confidence  :",
        f"{camera_confidence * 100:.1f}%"
    )


    print()
    print("--------------------------------")
    print("ULTRASONIC")
    print("--------------------------------")


    if distance is None:

        print(
            "Distance         : UNKNOWN"
        )

        print(
            "Path             : UNSAFE"
        )

    else:

        print(
            "Distance         :",
            f"{distance:.1f} cm"
        )


        if (
            distance
            >=
            SAFETY_DISTANCE_CM
        ):

            print(
                "Path             : CLEAR"
            )

        else:

            print(
                "Path             : BLOCKED"
            )


    print()
    print("--------------------------------")
    print("FUSION")
    print("--------------------------------")

    print(
        "Person confidence =",
        f"{fused_confidence * 100:.1f}%"
    )

    print(
        "Direction         =",
        direction
        if direction
        else
        "UNKNOWN"
    )

    print(
        "COMMAND           =",
        command
    )


    # Person status

    if (
        camera_person
        and
        fused_confidence >= 0.80
    ):

        print(
            "Person status     = CONFIRMED"
        )

    elif (
        camera_person
        and
        fused_confidence >= 0.60
    ):

        print(
            "Person status     = LIKELY"
        )

    elif camera_person:

        print(
            "Person status     = POSSIBLE"
        )

    else:

        print(
            "Person status     = "
            "AUDIO ALERT / "
            "VISUAL NOT CONFIRMED"
        )


    print("--------------------------------")


    return command


# ============================================================
# PROCESS ONE SPEECH EPISODE
# ============================================================

def process_episode(
    left_audio,
    right_audio,
    left_onset,
    right_onset,
    left_peak,
    right_peak,
    duration
):

    global rescue_locked_until


    print()
    print(
        ">>> SPEECH EPISODE COMPLETE"
    )


    print(
        f"Speech duration: "
        f"{duration:.2f} seconds"
    )


    # --------------------------------------------------------
    # Short speech filter
    # --------------------------------------------------------

    if (
        duration
        <
        MIN_SPEECH_SECONDS
    ):

        print(
            ">>> Speech too short - ignored"
        )

        return


    # --------------------------------------------------------
    # Direction
    # --------------------------------------------------------

    direction = (
        direction_from_mics(
            left_onset,
            right_onset,
            left_peak,
            right_peak
        )
    )


    print()

    print(
        ">>> MICROPHONE DIRECTION:",
        direction
        if direction
        else
        "UNKNOWN"
    )


    # --------------------------------------------------------
    # Convert audio to bytes
    # --------------------------------------------------------

    left_bytes = np.asarray(
        left_audio,
        dtype="<i2"
    ).tobytes()


    right_bytes = np.asarray(
        right_audio,
        dtype="<i2"
    ).tobytes()


    # --------------------------------------------------------
    # Vosk
    # --------------------------------------------------------

    left_text, left_confidence, left_match = (
        vosk_result(
            left_bytes
        )
    )


    right_text, right_confidence, right_match = (
        vosk_result(
            right_bytes
        )
    )


    print()
    print(
        "LEFT TEXT:"
    )

    print(
        left_text
    )

    print(
        "LEFT AUDIO CONFIDENCE:",
        f"{left_confidence * 100:.1f}%"
    )


    print()
    print(
        "RIGHT TEXT:"
    )

    print(
        right_text
    )

    print(
        "RIGHT AUDIO CONFIDENCE:",
        f"{right_confidence * 100:.1f}%"
    )


    # --------------------------------------------------------
    # Select strongest HELP evidence
    # --------------------------------------------------------

    if (
        left_match
        >=
        right_match
    ):

        selected_text = left_text
        selected_confidence = (
            left_confidence
        )
        selected_match = left_match

    else:

        selected_text = right_text
        selected_confidence = (
            right_confidence
        )
        selected_match = right_match


    # --------------------------------------------------------
    # HELP decision
    # --------------------------------------------------------

    help_detected = (
        selected_match >= 0.80
        and
        selected_confidence
        >=
        AUDIO_HELP_THRESHOLD
    )


    if not help_detected:

        print()
        print(
            ">>> NO HELP COMMAND"
        )

        return


    # --------------------------------------------------------
    # 20 SECOND LOCK
    # --------------------------------------------------------

    now = time.time()


    with rescue_lock:

        if (
            now
            <
            rescue_locked_until
        ):

            remaining = (
                rescue_locked_until
                -
                now
            )


            print()
            print(
                ">>> HELP DETECTED "
                "BUT 20-SECOND LOCK IS ACTIVE"
            )


            print(
                f">>> {remaining:.1f} "
                "seconds remaining"
            )


            return


        rescue_locked_until = (
            now
            +
            EVENT_LOCK_SECONDS
        )


    # --------------------------------------------------------
    # HELP EVENT
    # --------------------------------------------------------

    print()
    print(
        "================================"
    )

    print(
        "🚨 HELP COMMAND DETECTED"
    )

    print(
        "================================"
    )


    print(
        "Recognized:",
        selected_text
    )


    print(
        "Audio confidence:",
        f"{selected_confidence * 100:.1f}%"
    )


    # --------------------------------------------------------
    # Fusion
    # --------------------------------------------------------

    command = print_fusion(
        selected_confidence,
        direction
    )
    global active_help_command
    active_help_command = command

    print()
    print(
        ">>> DRONE COMMAND:",
        command
    )

    COMMAND_FILE = "/home/pii/rescue_drone/ai/latest_ai_command.txt"
    with open(COMMAND_FILE,"w") as f:
    	f.write(command + "\n")
    print(
        f">>> NEXT HELP EVENT "
        f"AVAILABLE IN "
        f"{EVENT_LOCK_SECONDS:.0f} SECONDS"
    )


# ============================================================
# STARTUP
# ============================================================

print(
    "=" * 64
)

print(
    "RESCUE DRONE - "
    "REAL-TIME SENSOR FUSION"
)

print(
    "=" * 64
)


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.isdir(
    VOSK_MODEL
):

    print(
        "ERROR: Vosk model not found:"
    )

    print(
        VOSK_MODEL
    )

    sys.exit(1)


if not os.path.isfile(
    YOLO_MODEL
):

    print(
        "ERROR: YOLO model not found:"
    )

    print(
        YOLO_MODEL
    )

    sys.exit(1)


# ============================================================
# VOSK
# ============================================================

print()
print(
    "Loading Vosk model..."
)

vosk_model = Model(
    VOSK_MODEL
)

print(
    "Vosk model loaded."
)


# ============================================================
# YOLO
# ============================================================

print()
print(
    "Loading YOLO11n..."
)


yolo_session = (
    ort.InferenceSession(
        YOLO_MODEL,
        providers=[
            "CPUExecutionProvider"
        ]
    )
)


yolo_input_name = (
    yolo_session
    .get_inputs()[0]
    .name
)


print(
    "YOLO11n loaded."
)


# ============================================================
# CAMERA
# ============================================================

print()
print(
    "Starting camera..."
)


try:

    picam2 = Picamera2()


    camera_config = (
        picam2
        .create_preview_configuration(
            main={
                "size": (
                    640,
                    480
                ),
                "format":
                "RGB888"
            }
        )
    )


    picam2.configure(
        camera_config
    )


    picam2.start()


    time.sleep(2)


    print(
        "Camera started."
    )


except Exception as error:

    print(
        "ERROR: Camera initialization failed:"
    )

    print(
        error
    )

    sys.exit(1)


# ============================================================
# ESP32 SERIAL
# ============================================================

print()
print(
    "Opening:",
    PORT
)


try:

    ser = serial.Serial(
        PORT,
        BAUD,
        timeout=0.1
    )


except Exception as error:

    print(
        "ERROR: ESP32 serial connection failed:"
    )

    print(
        error
    )

    picam2.stop()

    sys.exit(1)


time.sleep(1)

ser.reset_input_buffer()


print(
    "ESP32 connected."
)


# ============================================================
# BACKGROUND SERIAL THREAD
# ============================================================

serial_thread = threading.Thread(
    target=serial_reader,
    daemon=True
)

serial_thread.start()


# ============================================================
# BACKGROUND CAMERA THREAD
# ============================================================

camera_thread = threading.Thread(
    target=camera_loop,
    daemon=True
)

camera_thread.start()


# ============================================================
# MICROPHONE CALIBRATION
# ============================================================

print()

print(
    f"Keep quiet for "
    f"{CALIBRATION_SECONDS:.1f} "
    "seconds for microphone calibration."
)


calibration_left = []
calibration_right = []

calibration_start = time.time()


while (
    time.time()
    -
    calibration_start
    <
    CALIBRATION_SECONDS
):

    try:

        samples = (
            audio_queue.get(
                timeout=0.2
            )
        )

    except queue.Empty:

        continue


    calibration_left.append(
        rms(
            samples[:, 0]
        )
    )


    calibration_right.append(
        rms(
            samples[:, 1]
        )
    )


if calibration_left:

    left_background = float(
        np.median(
            calibration_left
        )
    )

else:

    left_background = 100.0


if calibration_right:

    right_background = float(
        np.median(
            calibration_right
        )
    )

else:

    right_background = 100.0


# Adaptive VAD thresholds

left_threshold = max(
    left_background * 2.0,
    250.0
)


right_threshold = max(
    right_background * 2.0,
    250.0
)


print()
print(
    "Microphone calibration complete."
)


print(
    f"LEFT background : "
    f"{left_background:.1f}"
)


print(
    f"RIGHT background: "
    f"{right_background:.1f}"
)


print(
    f"LEFT threshold  : "
    f"{left_threshold:.1f}"
)


print(
    f"RIGHT threshold : "
    f"{right_threshold:.1f}"
)


# ============================================================
# PRE-ROLL
# ============================================================

pre_roll_frames = int(
    SAMPLE_RATE
    *
    PRE_ROLL_SECONDS
)


left_pre = deque(
    maxlen=pre_roll_frames
)


right_pre = deque(
    maxlen=pre_roll_frames
)


# ============================================================
# SPEECH STATE
# ============================================================

speech_active = False

speech_start = 0.0

left_onset = None
right_onset = None

left_peak = 0.0
right_peak = 0.0

left_confirm = 0
right_confirm = 0

left_silent = 0
right_silent = 0

left_episode = []
right_episode = []


# ============================================================
# SYSTEM READY
# ============================================================

print()
print(
    "=" * 64
)

print(
    "REAL-TIME SYSTEM ACTIVE"
)

print(
    "=" * 64
)


print(
    f"Safety distance : "
    f"{SAFETY_DISTANCE_CM:.1f} cm"
)


print(
    f"Emergency stop  : "
    f"{EMERGENCY_STOP_CM:.1f} cm"
)


print(
    f"HELP lock       : "
    f"{EVENT_LOCK_SECONDS:.0f} seconds"
)


print()

print(
    "Waiting for:"
)

print(
    "  LEFT microphone"
)

print(
    "  RIGHT microphone"
)

print(
    "  Ultrasonic distance"
)

print(
    "  YOLO person detection"
)

print()


# ============================================================
# MAIN REAL-TIME LOOP
# ============================================================

last_status_update = 0.0
STATUS_UPDATE_SECONDS = 0.5

# Command produced by the current HELP event
active_help_command = "STOP"


try:

    while True:

        now = time.time()

        # ====================================================
        # SENSOR / NAVIGATION STATUS UPDATE
        # ====================================================

        if (
            now - last_status_update
            >= STATUS_UPDATE_SECONDS
        ):

            last_status_update = now

            distance = get_distance()

            camera_person, camera_confidence = (
                get_camera()
            )

            # ------------------------------------------------
            # OBSTACLE HAS HIGHEST PRIORITY
            # ------------------------------------------------

            obstacle = (
                distance is None
                or
                distance <= SAFETY_DISTANCE_CM
            )

            if obstacle:

                update_ai(
                    help_detected=False,
                    audio_confidence=0.0,
                    camera_person=camera_person,
                    camera_confidence=camera_confidence,
                    distance_cm=distance,
                    path="OBSTACLE",
                    fused_confidence=0.0,
                    direction="UNKNOWN",
                    command="STOP",
                    person_status=(
                        "OBSTACLE - STOP"
                    )
                )

                print()
                print(
                    ">>> 🚨 OBSTACLE - "
                    "EMERGENCY STOP"
                )

            else:

                # ------------------------------------------------
                # CHECK WHETHER HELP LOCK IS ACTIVE
                # ------------------------------------------------

                help_active = (
                    now
                    <
                    rescue_locked_until
                )

                if help_active:

                    # KEEP THE CURRENT HELP COMMAND.
                    # DO NOT overwrite it with STOP.

                    remaining = (
                        rescue_locked_until
                        -
                        now
                    )

                    print()
                    print(
                        ">>> HELP TRACKING ACTIVE"
                    )

                    print(
                        ">>> COMMAND:",
                        active_help_command
                    )

                    print(
                        ">>> TIME REMAINING:",
                        f"{remaining:.1f}s"
                    )

                else:

                    # ------------------------------------------------
                    # NO ACTIVE HELP EVENT
                    # NAVIGATION CONTROLLER CAN SEARCH
                    # ------------------------------------------------

                    active_help_command = "STOP"

                    update_ai(
                        help_detected=False,
                        audio_confidence=0.0,
                        camera_person=camera_person,
                        camera_confidence=camera_confidence,
                        distance_cm=distance,
                        path="CLEAR",
                        fused_confidence=(
                            fused_person_confidence(
                                0.0,
                                camera_person,
                                camera_confidence
                            )
                        ),
                        direction="UNKNOWN",
                        command="STOP",
                        person_status=(
                            "PERSON DETECTED"
                            if camera_person
                            else
                            "NO PERSON DETECTED"
                        )
                    )

                    print()
                    print(
                        ">>> NO ACTIVE HELP EVENT"
                    )

                    print(
                        ">>> NAVIGATION SEARCH ENABLED"
                    )

                    print(
                        ">>> PERSON:",
                        "YES"
                        if camera_person
                        else
                        "NO"
                    )

                    if distance is not None:

                        print(
                            ">>> DISTANCE:",
                            f"{distance:.1f} cm"
                        )

                    print(
                        ">>> COMMAND: STOP / SEARCH"
                    )


        # ====================================================
        # READ AUDIO
        # ====================================================

        try:

            samples = audio_queue.get(
                timeout=0.05
            )

        except queue.Empty:

            continue


        left = samples[:, 0]

        right = samples[:, 1]


        left_energy = rms(
            left
        )

        right_energy = rms(
            right
        )


        left_active = (
            left_energy
            >=
            left_threshold
        )

        right_active = (
            right_energy
            >=
            right_threshold
        )


        # ====================================================
        # CONTINUOUS PRE-ROLL
        # ====================================================

        for value in left:

            left_pre.append(
                int(value)
            )


        for value in right:

            right_pre.append(
                int(value)
            )


        # ====================================================
        # WAITING FOR SPEECH
        # ====================================================

        if not speech_active:

            if left_active:

                left_confirm += 1

            else:

                left_confirm = 0


            if right_active:

                right_confirm += 1

            else:

                right_confirm = 0


            # ------------------------------------------------
            # SPEECH START
            # ------------------------------------------------

            if (
                left_confirm
                >=
                ONSET_CONFIRM_CHUNKS
                or
                right_confirm
                >=
                ONSET_CONFIRM_CHUNKS
            ):

                speech_active = True

                speech_start = time.time()


                left_onset = (
                    speech_start
                    if left_active
                    else None
                )

                right_onset = (
                    speech_start
                    if right_active
                    else None
                )


                left_peak = left_energy

                right_peak = right_energy


                left_silent = 0

                right_silent = 0


                left_episode = list(
                    left_pre
                )

                right_episode = list(
                    right_pre
                )


                print()

                print(
                    ">>> SPEECH EPISODE START"
                )


                if left_active:

                    print(
                        ">>> LEFT "
                        "MICROPHONE ONSET"
                    )


                if right_active:

                    print(
                        ">>> RIGHT "
                        "MICROPHONE ONSET"
                    )


        # ====================================================
        # SPEECH ACTIVE
        # ====================================================

        else:

            left_episode.extend(
                left.tolist()
            )

            right_episode.extend(
                right.tolist()
            )


            left_peak = max(
                left_peak,
                left_energy
            )

            right_peak = max(
                right_peak,
                right_energy
            )


            now = time.time()


            # ------------------------------------------------
            # LATER LEFT ONSET
            # ------------------------------------------------

            if (
                left_active
                and
                left_onset is None
            ):

                left_onset = now

                print(
                    ">>> LEFT "
                    "MICROPHONE ONSET"
                )


            # ------------------------------------------------
            # LATER RIGHT ONSET
            # ------------------------------------------------

            if (
                right_active
                and
                right_onset is None
            ):

                right_onset = now

                print(
                    ">>> RIGHT "
                    "MICROPHONE ONSET"
                )


            # ------------------------------------------------
            # SILENCE COUNTERS
            # ------------------------------------------------

            if left_active:

                left_silent = 0

            else:

                left_silent += 1


            if right_active:

                right_silent = 0

            else:

                right_silent += 1


            duration = (
                now
                -
                speech_start
            )


            speech_finished = (
                left_silent
                >=
                SPEECH_END_CHUNKS
                and
                right_silent
                >=
                SPEECH_END_CHUNKS
            )


            force_finished = (
                duration
                >=
                MAX_SPEECH_SECONDS
            )


            # =================================================
            # END SPEECH EPISODE
            # =================================================

            if (
                speech_finished
                or
                force_finished
            ):

                process_episode(

                    left_episode,

                    right_episode,

                    left_onset,

                    right_onset,

                    left_peak,

                    right_peak,

                    duration

                )


                # ------------------------------------------------
                # RESET SPEECH STATE
                # ------------------------------------------------

                speech_active = False

                speech_start = 0.0

                left_onset = None

                right_onset = None

                left_peak = 0.0

                right_peak = 0.0

                left_confirm = 0

                right_confirm = 0

                left_silent = 0

                right_silent = 0

                left_episode = []

                right_episode = []


# ============================================================
# STOP WITH CTRL+C
# ============================================================

except KeyboardInterrupt:

    print()

    print(
        "Stopping rescue system..."
    )


finally:

    running = False

    try:

        serial_thread.join(
            timeout=1
        )

    except Exception:

        pass


    try:

        camera_thread.join(
            timeout=1
        )

    except Exception:

        pass


    try:

        ser.close()

        print(
            "ESP32 serial connection closed."
        )

    except Exception:

        pass


    try:

        picam2.stop()

        print(
            "Camera stopped."
        )

    except Exception:

        pass


    print()

    print(
        "=" * 64
    )

    print(
        "REAL-TIME RESCUE LOOP STOPPED"
    )

    print(
        "=" * 64
    )
