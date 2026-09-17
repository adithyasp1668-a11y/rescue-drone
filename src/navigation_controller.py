import time
import json
import os
from collections import deque


# ============================================================
# RESCUE DRONE NAVIGATION CONTROLLER
# STEP 8 - ZIG-ZAG + TARGET TRACKING + OBSTACLE RESUME
# SIMULATION + NAVIGATION COMMAND OUTPUT
# ============================================================


TELEMETRY_FILE = (
    "/home/pii/rescue_drone/ai/telemetry.json"
)
SITL_POSITION_FILE = (
    "/home/pii/rescue_drone/ai/sitl_position.json"
)
NAVIGATION_COMMAND_FILE = (
    "/home/pii/rescue_drone/ai/navigation_command.json"
)

RETURN_HOME_FILE = (
    "/home/pii/rescue_drone/ai/return_home.json"
)
# ============================================================
# SEARCH AREA
# ============================================================

SEARCH_LENGTH = 100.0
SEARCH_WIDTH = 100.0
LANE_SPACING = 5.0

SEARCH_SPEED = 1.0


# ============================================================
# AI CONFIDENCE
# ============================================================

LIKELY_THRESHOLD = 60.0
CONFIRMED_THRESHOLD = 70.0

HISTORY_SIZE = 5
REQUIRED_DETECTIONS = 3


# ============================================================
# ULTRASONIC SAFETY
# ============================================================

OBSTACLE_DISTANCE = 30.0
CAUTION_DISTANCE = 60.0


# ============================================================
# STATES
# ============================================================

SEARCH_ZIGZAG = "SEARCH_ZIGZAG"
TARGET_DETECTED = "TARGET_DETECTED"
TRACK_LEFT = "TRACK_LEFT"
TRACK_RIGHT = "TRACK_RIGHT"
APPROACH = "APPROACH"
HOLD = "HOLD"
AVOID = "AVOID"
RESUME_SEARCH="RESUME_SEARCH"
RTL = "RTL"


# ============================================================
# ACTIONS
# ============================================================

MOVE_RIGHT = "MOVE_RIGHT"
MOVE_LEFT = "MOVE_LEFT"
FORWARD = "FORWARD"
BACKWARD = "BACKWARD"
SHIFT_RIGHT = "SHIFT_RIGHT"

SHIFT = "SHIFT"

TRACK_TARGET_LEFT = "TRACK_LEFT"
TRACK_TARGET_RIGHT = "TRACK_RIGHT"

AVOID_LEFT = "AVOID_LEFT"
AVOID_RIGHT = "AVOID_RIGHT"

PAUSE_SEARCH = "PAUSE_SEARCH"

RETURN_TO_LAUNCH = "RETURN_TO_LAUNCH"


class ZigZagNavigator:

    def __init__(self):

        # ----------------------------------------------------
        # Navigation state
        # ----------------------------------------------------

        self.state = SEARCH_ZIGZAG

        self.action = "START"


        # ----------------------------------------------------
        # Position
        # ----------------------------------------------------

        self.x = 0.0
        self.y = 0.0


        # ----------------------------------------------------
        # Lane
        # ----------------------------------------------------

        self.lane = 1

        self.total_lanes = (
            int(SEARCH_WIDTH / LANE_SPACING)
            + 1
        )


        # ----------------------------------------------------
        # Search direction
        # ----------------------------------------------------

        self.direction = "RIGHT"


        # ----------------------------------------------------
        # AI history
        # ----------------------------------------------------

        self.confidence_history = deque(
            maxlen=HISTORY_SIZE
        )

        self.direction_history = deque(
            maxlen=HISTORY_SIZE
        )


        # ----------------------------------------------------
        # OBSTACLE AVOIDANCE MEMORY
        # ----------------------------------------------------

        # State before obstacle
        self.resume_state = SEARCH_ZIGZAG

        # Action before obstacle
        self.resume_action = MOVE_RIGHT

        # Search position before obstacle
        self.resume_x = 0.0
        self.resume_y = 0.0

        # Search lane before obstacle
        self.resume_lane = 1

        # Search direction before obstacle
        self.resume_direction = "RIGHT"

        # Avoidance direction
        self.avoid_direction = "RIGHT"

        # Number of avoidance cycles
        self.avoid_steps = 0

        # Number of cycles used while avoiding
        self.AVOID_STEPS = 3


        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print(
            "========================================"
        )

        print(
            " RESCUE DRONE NAVIGATION"
        )

        print(
            " STEP 8 - SEARCH + TARGET + AVOID"
        )

        print(
            "========================================"
        )

        print(
            f"Search Length : "
            f"{SEARCH_LENGTH:.1f} m"
        )

        print(
            f"Search Width  : "
            f"{SEARCH_WIDTH:.1f} m"
        )

        print(
            f"Lane Spacing  : "
            f"{LANE_SPACING:.1f} m"
        )

        print(
            f"Total Lanes   : "
            f"{self.total_lanes}"
        )

        print(
            "========================================"
        )


        # ----------------------------------------------------
        # Initial command
        # ----------------------------------------------------

        self.write_navigation_command()


    # ========================================================
    # NAVIGATION COMMAND OUTPUT
    # ========================================================

    def write_navigation_command(self):

        data = {

            "timestamp": time.time(),

            "action": str(
                self.action
            ),

            "state": str(
                self.state
            ),

            "x": float(
                self.x
            ),

            "y": float(
                self.y
            ),

            "lane": int(
                self.lane
            ),

            "direction": str(
                self.direction
            )
        }

        temp_file = NAVIGATION_COMMAND_FILE + ".tmp"

        try:

            # Write the complete JSON to a temporary file
            with open(
                temp_file,
                "w"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=2
                )

                file.flush()
                os.fsync(
                    file.fileno()
                )

            # Atomically replace the old command
            os.replace(
                temp_file,
                NAVIGATION_COMMAND_FILE
            )

        except Exception as e:

            print(
                "Navigation command write error:",
                e
            )

            # Remove temporary file if necessary
            try:

                if os.path.exists(
                    temp_file
                ):

                    os.remove(
                        temp_file
                    )

            except Exception:
                pass
        # ========================================================
    # READ REAL SITL POSITION
    # ========================================================

    def read_sitl_position(self):

        try:

            if not os.path.exists(
                SITL_POSITION_FILE
            ):
                return None

            with open(
                SITL_POSITION_FILE,
                "r"
            ) as file:

                position = json.load(file)

            return position

        except Exception as e:

            print(
                "SITL position read error:",
                e
            )

            return None

    # ========================================================
    # TELEMETRY
    # ========================================================

    def read_telemetry(self):

        try:

            if not os.path.exists(
                TELEMETRY_FILE
            ):

                print(
                    "WARNING: telemetry.json not found"
                )

                return None


            with open(
                TELEMETRY_FILE,
                "r"
            ) as file:

                return json.load(file)


        except Exception as e:

            print(
                "Telemetry read error:",
                e
            )

            return None
        # ========================================================
    # MANUAL RETURN HOME
    # ========================================================

    def check_return_home(self):

        try:

            if not os.path.exists(
                RETURN_HOME_FILE
            ):
                return False

            with open(
                RETURN_HOME_FILE,
                "r"
            ) as file:

                data = json.load(file)

            return bool(
                data.get(
                    "return_home",
                    False
                )
            )

        except Exception as e:

            print(
                "Return-home check error:",
                e
            )

            return False

    # ========================================================
    # SAFETY / OBSTACLE AVOIDANCE
    # ========================================================

    def obstacle_check(self, data):

        ultrasonic = data.get(
            "ultrasonic",
            {}
        )

        distance = float(
            ultrasonic.get(
                "distance_cm",
                999.0
            )
        )

        path = ultrasonic.get(
            "path",
            "UNKNOWN"
        )

        print(
            f"[SAFETY] "
            f"Distance: {distance:.1f} cm | "
            f"Path: {path}"
        )


        # ====================================================
        # OBSTACLE DETECTED
        # ====================================================

        if distance < OBSTACLE_DISTANCE:

            # ------------------------------------------------
            # FIRST ENTRY INTO AVOIDANCE
            # ------------------------------------------------

            if self.state != AVOID:

                print(
                    "!!! OBSTACLE DETECTED !!!"
                )

                print(
                    ">>> ENTERING OBSTACLE AVOIDANCE"
                )


                # --------------------------------------------
                # SAVE CURRENT NAVIGATION
                # --------------------------------------------

                self.resume_state = self.state

                self.resume_action = self.action

                self.resume_x = self.x

                self.resume_y = self.y

                self.resume_lane = self.lane

                self.resume_direction = (
                    self.direction
                )


                print(
                    ">>> ORIGINAL MOVEMENT SAVED"
                )

                print(
                    f">>> Resume Action: "
                    f"{self.resume_action}"
                )


                # --------------------------------------------
                # SELECT PERPENDICULAR AVOIDANCE
                # --------------------------------------------

                if self.resume_action == FORWARD:

                    # Forward obstacle:
                    # move sideways
                    self.avoid_direction = "LEFT"

                    self.action = AVOID_LEFT


                elif self.resume_action == BACKWARD:

                    # Backward obstacle:
                    # move sideways
                    self.avoid_direction = "RIGHT"

                    self.action = AVOID_RIGHT


                elif self.resume_action == SHIFT_RIGHT:

                    # Sideways movement:
                    # move longitudinally
                    self.avoid_direction = "FORWARD"

                    self.action = AVOID_FORWARD


                elif self.resume_action == TRACK_LEFT:

                    # Left tracking:
                    # move longitudinally
                    self.avoid_direction = "FORWARD"

                    self.action = AVOID_FORWARD


                elif self.resume_action == TRACK_RIGHT:

                    # Right tracking:
                    # move longitudinally
                    self.avoid_direction = "FORWARD"

                    self.action = AVOID_FORWARD


                elif self.resume_action == MOVE_LEFT:

                    self.avoid_direction = "FORWARD"

                    self.action = AVOID_FORWARD


                elif self.resume_action == MOVE_RIGHT:

                    self.avoid_direction = "FORWARD"

                    self.action = AVOID_FORWARD


                else:

                    # Safe fallback for an unknown
                    # original movement
                    self.avoid_direction = "LEFT"

                    self.action = AVOID_LEFT


                print(
                    f">>> AVOID ACTION: "
                    f"{self.action}"
                )

                print(
                    f">>> AVOID DIRECTION: "
                    f"{self.avoid_direction}"
                )


                self.avoid_steps = 0


            # ------------------------------------------------
            # CONTINUE AVOIDANCE
            # ------------------------------------------------

            self.state = AVOID

            self.avoid_steps += 1


            # ------------------------------------------------
            # KEEP THE SELECTED AVOIDANCE ACTION
            # ------------------------------------------------

            if self.resume_action == FORWARD:

                self.action = AVOID_LEFT


            elif self.resume_action == BACKWARD:

                self.action = AVOID_RIGHT


            elif (
                self.resume_action == SHIFT_RIGHT
                or self.resume_action == TRACK_LEFT
                or self.resume_action == TRACK_RIGHT
                or self.resume_action == MOVE_LEFT
                or self.resume_action == MOVE_RIGHT
            ):

                self.action = AVOID_FORWARD


            else:

                if self.avoid_direction == "RIGHT":

                    self.action = AVOID_RIGHT

                else:

                    self.action = AVOID_LEFT


            print(
                f">>> OBSTACLE AVOIDANCE "
                f"{self.avoid_steps}"
            )

            print(
                f">>> AVOID ACTION: "
                f"{self.action}"
            )


            self.write_navigation_command()

            return True


        # ====================================================
        # OBSTACLE CLEAR
        # ====================================================

        if self.state == AVOID:

            print(
                ">>> OBSTACLE CLEARED"
            )

            print(
                ">>> RESTORING PREVIOUS NAVIGATION"
            )


            # ------------------------------------------------
            # RESTORE SEARCH POSITION
            # ------------------------------------------------

            self.x = self.resume_x

            self.y = self.resume_y

            self.lane = self.resume_lane

            self.direction = (
                self.resume_direction
            )


            # ------------------------------------------------
            # RESTORE ORIGINAL STATE
            # ------------------------------------------------

            self.state = self.resume_state

            self.action = self.resume_action


            self.avoid_steps = 0


            print(
                ">>> ORIGINAL NAVIGATION RESTORED"
            )

            print(
                f">>> Resume Action: "
                f"{self.action}"
            )

            print(
                f">>> Lane: "
                f"{self.lane}/"
                f"{self.total_lanes}"
            )

            print(
                f">>> Position: "
                f"X={self.x:.1f} m | "
                f"Y={self.y:.1f} m"
            )


            self.write_navigation_command()

            return False


        # ====================================================
        # NO OBSTACLE
        # ====================================================

        return False

    # ========================================================
    # AI HISTORY
    # ========================================================

    def update_history(
        self,
        confidence,
        direction
    ):

        self.confidence_history.append(
            confidence
        )


        if direction in [
            "LEFT",
            "RIGHT"
        ]:

            self.direction_history.append(
                direction
            )


    # ========================================================
    # DOMINANT DIRECTION
    # ========================================================

    def get_direction(self):

        if not self.direction_history:

            return "UNKNOWN"


        left_count = (
            self.direction_history.count(
                "LEFT"
            )
        )


        right_count = (
            self.direction_history.count(
                "RIGHT"
            )
        )


        if left_count > right_count:

            return "LEFT"


        if right_count > left_count:

            return "RIGHT"


        return "UNKNOWN"


    # ========================================================
    # PROCESS AI
    # ========================================================

    def process_ai(self, data):

        fusion = data.get(
            "fusion",
            {}
        )


        confidence = float(
            fusion.get(
                "person_confidence",
                0.0
            )
        ) * 100


        direction = fusion.get(
            "direction",
            "UNKNOWN"
        )


        self.update_history(
            confidence,
            direction
        )


        likely_count = sum(
            1
            for value
            in self.confidence_history
            if value >= LIKELY_THRESHOLD
        )


        confirmed_count = sum(
            1
            for value
            in self.confidence_history
            if value >= CONFIRMED_THRESHOLD
        )


        dominant_direction = (
            self.get_direction()
        )


        print(
            f"[AI] Fusion: "
            f"{confidence:.1f}% | "
            f"Direction: {direction}"
        )


        print(
            f"[AI] Dominant: "
            f"{dominant_direction}"
        )


        # ----------------------------------------------------
        # CONFIRMED PERSON
        # ----------------------------------------------------

        if confirmed_count >= REQUIRED_DETECTIONS:

            print(
                ">>> TARGET CONFIRMED"
            )


            if dominant_direction == "LEFT":

                self.state = TRACK_LEFT

                self.action = (
                    TRACK_TARGET_LEFT
                )


            elif dominant_direction == "RIGHT":

                self.state = TRACK_RIGHT

                self.action = (
                    TRACK_TARGET_RIGHT
                )


            else:

                self.state = TARGET_DETECTED

                self.action = (
                    "TARGET_DETECTED"
                )


            self.write_navigation_command()

            return


        # ----------------------------------------------------
        # LIKELY PERSON
        # ----------------------------------------------------

        if likely_count >= REQUIRED_DETECTIONS:

            print(
                ">>> TARGET LIKELY"
            )

            print(
                ">>> PAUSING ZIG-ZAG"
            )


            self.state = TARGET_DETECTED

            self.action = PAUSE_SEARCH


            self.write_navigation_command()

            return


        # ----------------------------------------------------
        # NO CONFIRMED TARGET
        # ----------------------------------------------------

        self.state = SEARCH_ZIGZAG


    # ========================================================
    # SEARCH MOVEMENT
    # 100 m FORWARD/BACKWARD + 5 m RIGHT SHIFT
    # ========================================================

    def search_step(self):

        # ----------------------------------------------------
        # INITIALIZE SEARCH PHASE
        # ----------------------------------------------------

        if not hasattr(self, "search_phase"):
            self.search_phase = "FORWARD"

        # ----------------------------------------------------
        # FORWARD 100 m
        # ----------------------------------------------------

        if self.search_phase == "FORWARD":

            self.action = FORWARD

            self.x += SEARCH_SPEED

            if self.x >= SEARCH_LENGTH:

                self.x = SEARCH_LENGTH

                if self.y + LANE_SPACING <= SEARCH_WIDTH:
                    self.shift_target_y = self.y + LANE_SPACING
                    self.search_phase = "SHIFT_RIGHT"
                else:
                    self.action = RETURN_TO_LAUNCH

        elif self.search_phase == "SHIFT_RIGHT":

            # ------------------------------------------------
            # MOVE RIGHT 1 m PER SEARCH STEP
            # ------------------------------------------------

            self.action = SHIFT_RIGHT

            self.y += SEARCH_SPEED

            # ------------------------------------------------
            # STOP SHIFTING AFTER 5 m
            # ------------------------------------------------

            if self.y >= SEARCH_WIDTH:
                self.y = SEARCH_WIDTH

            # Check whether the complete 5 m lane shift
            # has been achieved.
            if self.y >= self.shift_target_y:

                self.y = self.shift_target_y

                self.lane += 1

                # ------------------------------------------------
                # ALTERNATE NEXT SEARCH DIRECTION
                # ------------------------------------------------

                if self.lane % 2 == 0:
                    self.search_phase = "BACKWARD"
                else:
                    self.search_phase = "FORWARD"
        # ----------------------------------------------------
        # BACKWARD 100 m
        # ----------------------------------------------------

        elif self.search_phase == "BACKWARD":

            self.action = BACKWARD

            self.x -= SEARCH_SPEED

            if self.x <= 0.0:

                self.x = 0.0

                if self.y + LANE_SPACING <= SEARCH_WIDTH:
                    self.shift_target_y=self.y + LANE_SPACING
                    self.search_phase = "SHIFT_RIGHT"
                else:
                    self.action = RETURN_TO_LAUNCH

        # ----------------------------------------------------
        # DISPLAY SEARCH POSITION
        # ----------------------------------------------------

        print(
            f"[SEARCH] "
            f"Lane {self.lane}/{self.total_lanes} | "
            f"Phase={self.search_phase} | "
            f"X={self.x:.1f} m | "
            f"Y={self.y:.1f} m | "
            f"Action={self.action}"
        )

        # ----------------------------------------------------
        # WRITE NAVIGATION COMMAND
        # ----------------------------------------------------

        self.write_navigation_command()

    # ========================================================
    # CHANGE LANE
    # ========================================================

    def change_lane(self):

        print(
            ">>> SEARCH BOUNDARY REACHED"
        )


        # ----------------------------------------------------
        # FINAL LANE
        # ----------------------------------------------------

        if self.lane >= self.total_lanes:

            print(
                ">>> SEARCH AREA EDGE REACHED"
            )

            print(
                ">>> RESTARTING ZIG-ZAG SEARCH"
            )

            # Start another search sweep
            # Do NOT return home automatically.

            self.lane = 1

            self.x = 0.0

            self.y = 0.0

                    # ----------------------------------------------------
            # OBSTACLE RECOVERY
            # ----------------------------------------------------

            self.resume_x = 0.0
            self.resume_y = 0.0
            self.avoid_direction = "RIGHT"
            self.avoid_steps = 0
            self.max_avoid_steps = 5
            self.direction = "RIGHT"

            self.state = SEARCH_ZIGZAG

            self.action = MOVE_RIGHT

            print(
                ">>> SEARCH CONTINUES"
            )

            print(
                f">>> Lane: "
                f"{self.lane}/"
                f"{self.total_lanes}"
            )

            print(
                f">>> Position: "
                f"X={self.x:.1f} m | "
                f"Y={self.y:.1f} m"
            )

            print(
                f">>> Direction: "
                f"{self.direction}"
            )

            self.write_navigation_command()

            return


        # ----------------------------------------------------
        # NEXT LANE
        # ----------------------------------------------------

        self.y += LANE_SPACING

        self.lane += 1


        self.action = SHIFT


        print(
            ">>> ACTION: SHIFT"
        )

        print(
            f">>> SHIFT TO Y="
            f"{self.y:.1f} m"
        )


        # ----------------------------------------------------
        # REVERSE SEARCH DIRECTION
        # ----------------------------------------------------

        if self.direction == "RIGHT":

            self.direction = "LEFT"

        else:

            self.direction = "RIGHT"


        print(
            f">>> NEXT LANE: "
            f"{self.lane}/"
            f"{self.total_lanes}"
        )

        print(
            f">>> NEXT DIRECTION: "
            f"{self.direction}"
        )


        self.write_navigation_command()


    # ========================================================
    # NAVIGATION STEP
    # ========================================================

    def navigation_step(self):

        # ----------------------------------------------------
        # MANUAL RETURN HOME HAS HIGHEST PRIORITY
        # ----------------------------------------------------

        if self.check_return_home():

            self.state = RTL

            self.action = RETURN_TO_LAUNCH

            print(
                "========================================"
            )

            print(
                ">>> MANUAL RETURN HOME COMMAND"
            )

            print(
                ">>> RETURN TO LAUNCH"
            )

            print(
                "========================================"
            )

            self.write_navigation_command()

            return


        data = self.read_telemetry()

        # ----------------------------------------------------
        # UPDATE FROM REAL SITL POSITION
        # ----------------------------------------------------

        # ----------------------------------------------------
        # READ REAL SITL POSITION FOR MONITORING ONLY
        # Do NOT overwrite navigation X/Y
        # ----------------------------------------------------

        sitl_position = self.read_sitl_position()

        if sitl_position is not None:

            sitl_x = float(
                sitl_position.get("x", 0.0)
            )

            sitl_y = float(
                sitl_position.get("y", 0.0)
            )
            sitl_z=float(
                sitl_position.get("z",0.0)
            )
            print(
            f"[SITL POSITION] "
            f"X={sitl_x:.2f} m | "
            f"Y={sitl_y:.2f} m | "
            f"y={sitl_z:.2f} m"
            )
        # ----------------------------------------------------
        # NO TELEMETRY
        # ----------------------------------------------------

        if data is None:
            print(
                ">>> NO TELEMETRY"
            )
            
            return



        # ----------------------------------------------------
        # SAFETY FIRST
        # ----------------------------------------------------

        obstacle = self.obstacle_check(
            data
        )


        if obstacle:

            print(
                ">>> NORMAL NAVIGATION PAUSED"
            )

            return


        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        self.process_ai(
            data
        )


        # ----------------------------------------------------
        # STATE MACHINE
        # ----------------------------------------------------

        if self.state == SEARCH_ZIGZAG:

            self.search_step()


        elif self.state == TARGET_DETECTED:

            print(
                ">>> TARGET DETECTED"
            )

            print(
                ">>> SEARCH PAUSED"
            )

            self.write_navigation_command()


        elif self.state == TRACK_LEFT:

            print(
                ">>> TRACK TARGET LEFT"
            )

            self.write_navigation_command()


        elif self.state == TRACK_RIGHT:

            print(
                ">>> TRACK TARGET RIGHT"
            )

            self.write_navigation_command()


        elif self.state == APPROACH:

            print(
                ">>> APPROACH TARGET"
            )

            self.write_navigation_command()


        elif self.state == HOLD:

            print(
                ">>> HOLD POSITION"
            )

            self.write_navigation_command()


        elif self.state == AVOID:

            if self.action == AVOID_RIGHT:

                print(
                    ">>> MOVING RIGHT "
                    "AROUND OBSTACLE"
                )

            elif self.action == AVOID_LEFT:

                print(
                    ">>> MOVING LEFT "
                    "AROUND OBSTACLE"
                )

            self.write_navigation_command()


        elif self.state == RTL:

            print(
                ">>> RETURN TO LAUNCH"
            )

            self.write_navigation_command()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    navigator = ZigZagNavigator()


    print(
        "\nStarting rescue navigation...\n"
    )


    try:

        while True:

            navigator.navigation_step()


            if navigator.state == RTL:

                break


            time.sleep(0.2)


    except KeyboardInterrupt:

        print(
            "\nStopping navigation..."
        )


        navigator.action = "STOP"

        navigator.write_navigation_command()


        print(
            "Navigation stopped."
        )
