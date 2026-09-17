from pymavlink import mavutil
from telemetry import update_motors
import time
import json
import os

PORT = "/dev/ttyACM0"
BAUD = 115200

COMMAND_FILE = "/home/pii/rescue_drone/ai/navigation_command.json"

# ============================================================
# BENCH MOTOR TEST ONLY
#
# PROPELLERS MUST BE REMOVED
#
# Motor layout:
#
#             FRONT
#
#       M1 CCW       M3 CW
#
#
#       M4 CW        M2 CCW
#
#             REAR
#
# ============================================================

print("=" * 60)
print("BENCH MOTOR TEST - NAVIGATION COMMANDS")
print("=" * 60)

print()
print("SAFETY:")
print("PROPELLERS MUST BE REMOVED")
print("BENCH TEST ONLY")
print("DO NOT USE THIS FILE FOR ACTUAL FLIGHT")
print()

print("Connecting to Pixhawk...")

master = mavutil.mavlink_connection(
    PORT,
    baud=BAUD
)

master.wait_heartbeat()

print("PIXHAWK CONNECTED")
print("System:", master.target_system)
print("Component:", master.target_component)


# ============================================================
# BENCH PATTERNS
# ============================================================

# FORWARD
#
# Front motors lower
# Rear motors higher
#
FORWARD_PATTERN = {
    1: 12,   # Front Left
    2: 18,   # Rear Right
    3: 12,   # Front Right
    4: 18    # Rear Left
}


# BACKWARD
#
# Front motors higher
# Rear motors lower
#
BACKWARD_PATTERN = {
    1: 18,
    2: 12,
    3: 18,
    4: 12
}


# SHIFT RIGHT
#
# Left motors higher
# Right motors lower
#
SHIFT_RIGHT_PATTERN = {
    1: 18,   # Front Left
    2: 12,   # Rear Right
    3: 12,   # Front Right
    4: 18    # Rear Left
}


# TRACK LEFT
#
# Bench demonstration of forward + left
#
TRACK_LEFT_PATTERN = {
    1: 12,
    2: 18,
    3: 15,
    4: 15
}


# TRACK RIGHT
#
# Bench demonstration of forward + right
#
TRACK_RIGHT_PATTERN = {
    1: 15,
    2: 15,
    3: 12,
    4: 18
}

# ============================================================
# OBSTACLE AVOIDANCE PATTERNS
# ============================================================

# AVOID LEFT
#
# Left motors lower
# Right motors higher
#
AVOID_LEFT_PATTERN = {
    1: 12,   # Front Left
    2: 18,   # Rear Right
    3: 18,   # Front Right
    4: 12    # Rear Left
}


# AVOID RIGHT
#
# Left motors higher
# Right motors lower
#
AVOID_RIGHT_PATTERN = {
    1: 18,   # Front Left
    2: 12,   # Rear Right
    3: 12,   # Front Right
    4: 18    # Rear Left
}


# AVOID FORWARD
#
# Same bench differential as FORWARD
#
AVOID_FORWARD_PATTERN = {
    1: 12,
    2: 18,
    3: 12,
    4: 18
}


# AVOID BACKWARD
#
# Same bench differential as BACKWARD
#
AVOID_BACKWARD_PATTERN = {
    1: 18,
    2: 12,
    3: 18,
    4: 12
}


# ============================================================
# BENCH HOLD / IDLE
# ============================================================

# IMPORTANT:
# This is only a bench-test value.
# It is NOT a guaranteed airborne hover throttle.
#
BENCH_HOLD_THROTTLE = 13

HOLD_PATTERN = {
    1: BENCH_HOLD_THROTTLE,
    2: BENCH_HOLD_THROTTLE,
    3: BENCH_HOLD_THROTTLE,
    4: BENCH_HOLD_THROTTLE
}
# TRUE STOP
#
# No motor-test command is sent when STOP is active.
#
STOP_PATTERN = {
    1: 0,
    2: 0,
    3: 0,
    4: 0
}


# ============================================================
# MOTOR TEST
# ============================================================

def motor_test(motor, throttle, duration=0.5):

    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_DO_MOTOR_TEST,

        0,

        motor,
        0,
        throttle,
        duration,
        1,
        0,
        0
    )


# ============================================================
# STOP
# ============================================================

def stop_motors():

    print("MOTORS: STOP")

    update_motors(
        command="STOP",
        angle=0,
        m1=0,
        m2=0,
        m3=0,
        m4=0
    )

last_pattern = None
# ============================================================
# APPLY BENCH PATTERN
# ============================================================

def apply_pattern(pattern, command_name):
    global last_pattern

    last_pattern = pattern.copy()
    print()
    print("=" * 50)
    print("BENCH COMMAND:", command_name)
    print("=" * 50)

    print(
        f"M1={pattern[1]}%  "
        f"M2={pattern[2]}%  "
        f"M3={pattern[3]}%  "
        f"M4={pattern[4]}%"
    )

    # Send each motor test command
    for motor in [1, 2, 3, 4]:

        motor_test(
            motor,
            pattern[motor],
            0.5
        )

        time.sleep(0.02)

    # Dashboard telemetry
    if command_name == "TRACK_LEFT":
        angle = -30

    elif command_name == "TRACK_RIGHT":
        angle = 30

    elif command_name == "SHIFT_RIGHT":
        angle = 90

    elif command_name == "FORWARD":
        angle = 0

    elif command_name == "BACKWARD":
        angle = 180

    else:
        angle = 0

    update_motors(
        command=command_name,
        angle=angle,
        m1=pattern[1],
        m2=pattern[2],
        m3=pattern[3],
        m4=pattern[4]
    )


# ============================================================
# READ NAVIGATION COMMAND
# ============================================================

def read_command():

    try:

        if not os.path.exists(COMMAND_FILE):
            return "STOP"

        with open(COMMAND_FILE, "r") as f:

            data = json.load(f)

        action = str(
            data.get("action", "STOP")
        ).upper()

        if action == "":
            return "STOP"

        return action

    except Exception as e:

        print(
            "Command read error:",
            e
        )
        #IMPORTANT
        #NEVER convert a temporary JSON read error into STOP
        #keep the last valid motor command
        return None


# ============================================================
# MAIN LOOP
# ============================================================

last_command = None

print()
print("Waiting for navigation command...")
print()
print("Supported commands:")
print("FORWARD")
print("BACKWARD")
print("SHIFT_RIGHT")
print("TRACK_LEFT")
print("TRACK_RIGHT")
print("STOP")
print("RETURN_TO_LAUNCH")
print()
print("CTRL+C = stop bench test")
print()


try:

        while True:

            command = read_command()

            # ----------------------------------------------------
            # JSON TEMPORARILY UNAVAILABLE
            # HOLD LAST VALID MOTOR COMMAND
            # ----------------------------------------------------

            if command is None:

                if last_pattern is not None:

                    for motor in [1, 2, 3, 4]:

                        motor_test(
                            motor,
                            last_pattern[motor],
                            0.5
                        )

                        time.sleep(0.02)

                time.sleep(0.2)
                continue


            # ----------------------------------------------------
            # PROCESS NEW COMMAND
            # ----------------------------------------------------

            if command != last_command:

                print()
                print(
                    "NEW NAVIGATION COMMAND:",
                    command
                )


                # =================================================
                # NORMAL SEARCH
                # =================================================

                if command == "FORWARD":

                    apply_pattern(
                        FORWARD_PATTERN,
                        "FORWARD"
                    )


                elif command == "BACKWARD":

                    apply_pattern(
                        BACKWARD_PATTERN,
                        "BACKWARD"
                    )


                elif command == "SHIFT_RIGHT":

                    apply_pattern(
                        SHIFT_RIGHT_PATTERN,
                        "SHIFT_RIGHT"
                    )


                # =================================================
                # TARGET TRACKING
                # =================================================

                elif command == "TRACK_LEFT":

                    apply_pattern(
                        TRACK_LEFT_PATTERN,
                        "TRACK_LEFT"
                    )


                elif command == "TRACK_RIGHT":

                    apply_pattern(
                        TRACK_RIGHT_PATTERN,
                        "TRACK_RIGHT"
                    )


                # =================================================
                # OBSTACLE AVOIDANCE
                # =================================================

                elif command == "AVOID_LEFT":

                    apply_pattern(
                        AVOID_LEFT_PATTERN,
                        "AVOID_LEFT"
                    )


                elif command == "AVOID_RIGHT":

                    apply_pattern(
                        AVOID_RIGHT_PATTERN,
                        "AVOID_RIGHT"
                    )


                elif command == "AVOID_FORWARD":

                    apply_pattern(
                        AVOID_FORWARD_PATTERN,
                        "AVOID_FORWARD"
                    )


                elif command == "AVOID_BACKWARD":

                    apply_pattern(
                        AVOID_BACKWARD_PATTERN,
                        "AVOID_BACKWARD"
                    )


                # =================================================
                # HOLD / STOP
                # =================================================

                elif command == "STOP":

                    apply_pattern(
                        HOLD_PATTERN,
                        "STOP / HOLD"
                    )


                # =================================================
                # RETURN TO LAUNCH
                # =================================================

                elif command == "RETURN_TO_LAUNCH":

                    print(
                        "RETURN_TO_LAUNCH received"
                    )

                    print(
                        "Bench test: HOLDING PREVIOUS MOTOR COMMAND"
                    )

                    if last_pattern is not None:

                        apply_pattern(
                            last_pattern,
                            "RETURN_TO_LAUNCH - HOLD PREVIOUS"
                        )

                    else:

                        apply_pattern(
                            HOLD_PATTERN,
                            "RETURN_TO_LAUNCH - HOLD"
                        )


                # =================================================
                # UNKNOWN COMMAND
                # =================================================

                else:

                    print(
                        "UNKNOWN COMMAND:"
                        f" {command}"
                    )

                    print(
                        "Holding previous valid motor command"
                    )

                last_command = command


            # ----------------------------------------------------
            # CONTINUOUSLY REFRESH ACTIVE PATTERN
            # ----------------------------------------------------

            if last_pattern is not None:

                for motor in [1, 2, 3, 4]:

                    motor_test(
                        motor,
                        last_pattern[motor],
                        0.5
                    )

                    time.sleep(0.02)


            time.sleep(0.2)
        # ----------------------------------------------------
        # Refresh active motor pattern
        #
        # MAV_CMD_DO_MOTOR_TEST expires, so repeat it.
        # ----------------------------------------------------

        if command == "FORWARD":

            apply_pattern(
                FORWARD_PATTERN,
                "FORWARD"
            )

        elif command == "BACKWARD":

            apply_pattern(
                BACKWARD_PATTERN,
                "BACKWARD"
            )

        elif command == "SHIFT_RIGHT":

            apply_pattern(
                SHIFT_RIGHT_PATTERN,
                "SHIFT_RIGHT"
            )

        elif command == "TRACK_LEFT":

            apply_pattern(
                TRACK_LEFT_PATTERN,
                "TRACK_LEFT"
            )

        elif command == "TRACK_RIGHT":

            apply_pattern(
                TRACK_RIGHT_PATTERN,
                "TRACK_RIGHT"
            )

        elif command in [
            "STOP",
            "RETURN_TO_LAUNCH"
        ]:

            stop_motors()

        time.sleep(0.05)


except KeyboardInterrupt:

    print()
    print("CTRL+C detected.")


finally:

    stop_motors()

    print(
        "Stopping motor bench test..."
    )

    master.close()

    print(
        "Pixhawk connection closed."
    )
