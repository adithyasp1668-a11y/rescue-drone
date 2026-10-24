from rplidar import RPLidar
import time
import json
import os

PORT = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0-port0"
BAUDRATE = 115200

STOP_DISTANCE_MM = 150.0
CLEAR_DISTANCE_MM = 300.0

OUTPUT_FILE = "/home/pii/rescue_drone/ai/lidar_telemetry.json"

PRINT_INTERVAL = 0.5
RESTART_DELAY = 2.0


def sector(angle):
    angle = float(angle) % 360.0

    if angle >= 330.0 or angle <= 30.0:
        return "front"

    if 30.0 < angle < 150.0:
        return "left"

    if 210.0 < angle < 330.0:
        return "right"

    return "rear"


def write_telemetry(front_mm, left_mm, right_mm, status):
    data = {
        "timestamp": time.time(),

        "front_mm": round(float(front_mm), 1),
        "front_cm": round(float(front_mm) / 10.0, 1),

        "left_mm": round(float(left_mm), 1),
        "left_cm": round(float(left_mm) / 10.0, 1),

        "right_mm": round(float(right_mm), 1),
        "right_cm": round(float(right_mm) / 10.0, 1),

        "status": status
    }

    temp_file = OUTPUT_FILE + ".tmp"

    with open(temp_file, "w") as f:
        json.dump(data, f)

    os.replace(temp_file, OUTPUT_FILE)


def run_one_session():

    lidar = None

    try:

        print()
        print("=" * 60)
        print("RPLIDAR CONTINUOUS OBSTACLE MONITOR")
        print("=" * 60)
        print("PORT:", PORT)
        print("STOP:", STOP_DISTANCE_MM / 1000.0, "m")
        print("CLEAR:", CLEAR_DISTANCE_MM / 1000.0, "m")
        print()

        lidar = RPLidar(
            PORT,
            baudrate=BAUDRATE,
            timeout=3
        )

        # Clean stale bytes before starting.
        try:
            lidar.clean_input()
        except Exception:
            pass

        time.sleep(0.3)

        # Get device information.
        try:
            print(
                "LiDAR INFO:",
                lidar.get_info()
            )
        except Exception as e:
            print(
                "INFO warning:",
                e
            )

        # Get health information.
        try:
            print(
                "LiDAR HEALTH:",
                lidar.get_health()
            )
        except Exception as e:
            print(
                "HEALTH warning:",
                e
            )

        print("Starting LiDAR motor...")
        lidar.start_motor()

        time.sleep(1.0)

        print("Continuous scanning started.")
        print("Press Ctrl+C to stop.")
        print()

        last_print = 0.0

        # IMPORTANT:
        # Disable the library's automatic input-buffer limit.
        # This prevents the 3990/500 restart problem.
        for scan in lidar.iter_scans(
            max_buf_meas=False,
            min_len=5
        ):

            front_values = []
            left_values = []
            right_values = []

            for measurement in scan:

                if len(measurement) < 3:
                    continue

                quality = float(measurement[0])
                angle = float(measurement[1])
                distance_mm = float(measurement[2])

                if quality <= 0:
                    continue

                if distance_mm <= 0:
                    continue

                area = sector(angle)

                if area == "front":
                    front_values.append(distance_mm)

                elif area == "left":
                    left_values.append(distance_mm)

                elif area == "right":
                    right_values.append(distance_mm)

            if not front_values:
                continue

            front_mm = min(front_values)

            left_mm = (
                min(left_values)
                if left_values
                else 99999.0
            )

            right_mm = (
                min(right_values)
                if right_values
                else 99999.0
            )

            # ==============================================
            # CHECK ALL THREE DIRECTIONS
            # ==============================================

            blocked_sectors = []

            # Front obstacle
            if front_mm <= STOP_DISTANCE_MM:
                blocked_sectors.append("FRONT")

            # Left obstacle
            if left_mm <= STOP_DISTANCE_MM:
                blocked_sectors.append("LEFT")

            # Right obstacle
            if right_mm <= STOP_DISTANCE_MM:
                blocked_sectors.append("RIGHT")


            # ==============================================
            # OVERALL STATUS
            # ==============================================

            if blocked_sectors:

                status = "STOP"

            elif (
                front_mm < CLEAR_DISTANCE_MM
                or left_mm < CLEAR_DISTANCE_MM
                or right_mm < CLEAR_DISTANCE_MM
            ):

                status = "CAUTION"

            else:

                status = "CLEAR"

            write_telemetry(
                front_mm,
                left_mm,
                right_mm,
                status
            )

            now = time.time()

            if now - last_print >= PRINT_INTERVAL:

                blocked_text = (
                    ",".join(blocked_sectors)
                    if blocked_sectors
                    else "NONE"
                )

                print(
                    f"FRONT: {front_mm / 1000.0:.2f} m | "
                    f"LEFT: {left_mm / 1000.0:.2f} m | "
                    f"RIGHT: {right_mm / 1000.0:.2f} m | "
                    f"BLOCKED: {blocked_text} | "
                    f"STATUS: {status}"
                )
                last_print = now

    except KeyboardInterrupt:

        raise

    except Exception as e:

        print()
        print("LiDAR session error:", e)
        print("Restarting LiDAR session...")

    finally:

        if lidar is not None:

            try:
                lidar.stop()
            except Exception:
                pass

            try:
                lidar.stop_motor()
            except Exception:
                pass

            try:
                lidar.disconnect()
            except Exception:
                pass


# ==========================================================
# PERMANENT LOOP
# ==========================================================

while True:

    try:

        run_one_session()

    except KeyboardInterrupt:

        print()
        print(">>> Ctrl+C received.")
        print(">>> LiDAR monitor stopped.")
        break

    except Exception as e:

        print()
        print(">>> Monitor error:", e)

    print(
        f">>> Restarting in {RESTART_DELAY:.1f} seconds..."
    )

    time.sleep(RESTART_DELAY)
