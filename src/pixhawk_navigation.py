import json
import time
from pymavlink import mavutil


# ============================================================
# RESCUE DRONE PIXHAWK NAVIGATION BRIDGE
# STEP 18
# REAL PIXHAWK MODE
#
# Reads:
#     navigation_command.json
#
# Sends:
#     MAVLink velocity commands to REAL PIXHAWK
#
# IMPORTANT:
# This is for SITL testing.
# Do NOT connect to the real drone yet.
# ============================================================


# ============================================================
# CONNECTION
# ============================================================

PIXHAWK_CONNECTION = "/dev/ttyACM0"

# ============================================================
# NAVIGATION COMMAND FILE
# ============================================================

NAVIGATION_COMMAND_FILE = (
    "/home/pii/rescue_drone/ai/navigation_command.json"
)


# ============================================================
# SPEED SETTINGS
# ============================================================

SEARCH_SPEED = 0.30
TRACK_FORWARD_SPEED = 0.30
TRACK_SIDE_SPEED = 0.30

AVOID_SPEED = 0.30

SHIFT_SPEED = 0.30


# ============================================================
# MAVLINK CONNECTION
# ============================================================

print(
    "========================================"
)

print(
    " RESCUE DRONE PIXHAWK NAVIGATION"
)

print(
    " SITL MODE"
)

print(
    "========================================"
)

print(
    "Connecting to REAL PIXHAWK..."
)


master = mavutil.mavlink_connection(
    PIXHAWK_CONNECTION,
    baud=115200
)

print(
    "Waiting for heartbeat..."
)


master.wait_heartbeat()


print(
    "========================================"
)

print(
    "REAL PIXHAWK CONNECTION SUCCESS"
)

print(
    f"System ID  : {master.target_system}"
)

print(
    f"Component ID: {master.target_component}"
)

print(
    "========================================"
)


# ============================================================
# VELOCITY COMMAND
# ============================================================

def send_velocity(
    forward=0.0,
    right=0.0
):

    """
    Send velocity using BODY_OFFSET_NED.

    forward:
        + = forward

    right:
        + = right

    z velocity is zero.
    """

    master.mav.set_position_target_local_ned_send(

        0,

        master.target_system,
        master.target_component,

        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,

        0b0000111111000111,

        0,
        0,
        0,

        forward,
        right,
        0,

        0,
        0,
        0,

        0,
        0
    )


# ============================================================
# STOP
# ============================================================

def stop_vehicle():

    send_velocity(
        forward=0.0,
        right=0.0
    )


# ============================================================
# READ NAVIGATION COMMAND
# ============================================================

def read_navigation_command():

    try:

        with open(
            NAVIGATION_COMMAND_FILE,
            "r"
        ) as file:

            return json.load(file)

    except Exception:

        return None


# ============================================================
# EXECUTE NAVIGATION ACTION
# ============================================================

def execute_action(action, direction="RIGHT"):

    # --------------------------------------------------------
    # SEARCH FORWARD
    # --------------------------------------------------------

    if action == "FORWARD":

        send_velocity(
            forward=SEARCH_SPEED,
            right=0.0
        )

        print(
            "ACTION: SEARCH FORWARD"
        )


    # --------------------------------------------------------
    # SEARCH BACKWARD
    # --------------------------------------------------------

    elif action == "BACKWARD":

        send_velocity(
            forward=-SEARCH_SPEED,
            right=0.0
        )

        print(
            "ACTION: SEARCH BACKWARD"
        )


    # --------------------------------------------------------
    # SHIFT RIGHT
    # --------------------------------------------------------

    elif action == "SHIFT_RIGHT":

        send_velocity(
            forward=0.0,
            right=SHIFT_SPEED
        )

        print(
            "ACTION: SHIFT RIGHT"
        )


    # --------------------------------------------------------
    # TRACK TARGET LEFT
    # --------------------------------------------------------

    elif action == "TRACK_LEFT":

        send_velocity(
            forward=TRACK_FORWARD_SPEED,
            right=-TRACK_SIDE_SPEED
        )

        print(
            "ACTION: TRACK TARGET LEFT"
        )


    # --------------------------------------------------------
    # TRACK TARGET RIGHT
    # --------------------------------------------------------

    elif action == "TRACK_RIGHT":

        send_velocity(
            forward=TRACK_FORWARD_SPEED,
            right=TRACK_SIDE_SPEED
        )

        print(
            "ACTION: TRACK TARGET RIGHT"
        )

    # --------------------------------------------------------
    # APPROACH
    # --------------------------------------------------------

    elif action == "APPROACH":

        send_velocity(
            forward=TRACK_FORWARD_SPEED,
            right=0.0
        )

        print(
            "ACTION: APPROACH TARGET"
        )


    # --------------------------------------------------------
    # OBSTACLE AVOID LEFT
    # --------------------------------------------------------

    elif action == "AVOID_LEFT":

        send_velocity(
            forward=0.0,
            right=-AVOID_SPEED
        )

        print(
            "ACTION: AVOID OBSTACLE LEFT"
        )


    # --------------------------------------------------------
    # OBSTACLE AVOID RIGHT
    # --------------------------------------------------------

    elif action == "AVOID_RIGHT":

        send_velocity(
            forward=0.0,
            right=AVOID_SPEED
        )

        print(
            "ACTION: AVOID OBSTACLE RIGHT"
        )


    # --------------------------------------------------------
    # PAUSE / HOLD / TARGET DETECTED
    # --------------------------------------------------------

    elif action in [
        "PAUSE_SEARCH",
        "TARGET_DETECTED",
        "HOLD",
        "START",
        "STOP"
    ]:

        stop_vehicle()

        print(
            f"ACTION: {action} -> STOP/HOLD"
        )


    # --------------------------------------------------------
    # RTL
    # --------------------------------------------------------

    elif action == "RETURN_TO_LAUNCH":

        stop_vehicle()

        print(
            "ACTION: RETURN TO LAUNCH"
        )

        master.mav.command_long_send(

            master.target_system,
            master.target_component,

            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,

            0,

            0,
            0,
            0,
            0,
            0,
            0,
            0
        )


    # --------------------------------------------------------
    # AVOID FALLBACK
    # --------------------------------------------------------

    elif action == "AVOID":

        stop_vehicle()

        print(
            "ACTION: AVOID -> STOP SAFELY"
        )


    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------

    else:

        stop_vehicle()

        print(
            f"ACTION: UNKNOWN ({action}) -> STOP"
        )


# ============================================================
# MAIN LOOP
# ============================================================

last_action = None


try:

    while True:

        command = read_navigation_command()


        if command is None:

            stop_vehicle()

            time.sleep(0.2)

            continue


        action = command.get(
            "action",
            "STOP"
        )


        state = command.get(
            "state",
            "UNKNOWN"
        )


        x = command.get(
            "x",
            0.0
        )


        y = command.get(
            "y",
            0.0
        )


        lane = command.get(
            "lane",
            0
        )


        direction = command.get(
            "direction",
            "RIGHT"
        )


        # ----------------------------------------------------
        # DISPLAY WHEN ACTION CHANGES
        # ----------------------------------------------------

        if action != last_action:

            print(
                "----------------------------------------"
            )

            print(
                f"Navigation action: {action}"
            )

            print(
                f"State: {state}"
            )

            print(
                f"Position: X={x:.1f} "
                f"Y={y:.1f}"
            )

            print(
                f"Lane: {lane}"
            )

            print(
                f"Direction: {direction}"
            )


            last_action = action


        # ----------------------------------------------------
        # SEND COMMAND
        # ----------------------------------------------------

        execute_action(
            action,
            direction
        )


        # ----------------------------------------------------
        # SEND FREQUENTLY
        # ----------------------------------------------------

        time.sleep(0.2)


except KeyboardInterrupt:

    print(
        "\nCOMMAND TIMEOUT - STOPPING NAVIGATION"
    )

    stop_vehicle()
