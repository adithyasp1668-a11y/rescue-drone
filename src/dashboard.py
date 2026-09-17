from flask import Flask, jsonify, render_template, send_file
import json
import os
import time

app = Flask(__name__)

BASE_DIR = "/home/pii/rescue_drone/ai"

AI_FILE = os.path.join(
    BASE_DIR,
    "telemetry.json"
)

MOTOR_FILE = os.path.join(
    BASE_DIR,
    "motor_telemetry.json"
)

NAVIGATION_FILE = os.path.join(
    BASE_DIR,
    "navigation_command.json"
)

RETURN_HOME_FILE = os.path.join(
    BASE_DIR,
    "return_home.json"
)


# ============================================================
# READ JSON SAFELY
# ============================================================

def read_json(filename):

    try:

        with open(
            filename,
            "r"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


# ============================================================
# WRITE RETURN HOME COMMAND
# ============================================================

def write_return_home():

    data = {
        "return_home": True,
        "timestamp": time.time()
    }

    temp_file = RETURN_HOME_FILE + ".tmp"

    try:

        with open(
            temp_file,
            "w"
        ) as f:

            json.dump(
                data,
                f,
                indent=2
            )

            f.flush()
            os.fsync(
                f.fileno()
            )

        os.replace(
            temp_file,
            RETURN_HOME_FILE
        )

        return True

    except Exception as e:

        print(
            "Return-home write error:",
            e
        )

        try:

            if os.path.exists(
                temp_file
            ):

                os.remove(
                    temp_file
                )

        except Exception:
            pass

        return False

@app.route("/camera")
def camera():
    return send_file(
        "/home/pii/rescue_drone/ai/latest_camera.jpg",
        mimetype="image/jpeg"
    )

# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def index():

    return render_template(
        "dashboard.html"
    )


# ============================================================
# LIVE TELEMETRY
# ============================================================

@app.route("/api/telemetry")
def telemetry():

    ai = read_json(
        AI_FILE
    )

    motors = read_json(
        MOTOR_FILE
    )

    navigation = read_json(
        NAVIGATION_FILE
    )

    return_home = read_json(
        RETURN_HOME_FILE
    )

    return jsonify({

        "ai": ai,

        "motors": motors,

        "navigation": navigation,

        "return_home": return_home

    })


# ============================================================
# RETURN TO HOME BUTTON
# ============================================================

@app.route(
    "/api/return-home",
    methods=["POST"]
)
def return_home():

    success = write_return_home()

    if success:

        return jsonify({
            "success": True,
            "message":
                "RETURN TO HOME REQUEST SENT"
        })

    return jsonify({
        "success": False,
        "message":
            "FAILED TO SEND RETURN HOME REQUEST"
    }), 500
# ============================================================
# CANCEL RETURN TO HOME
# ============================================================

@app.route(
    "/api/cancel-return-home",
    methods=["POST"]
)
def cancel_return_home():

    try:

        data = {
            "return_home": False,
            "timestamp": time.time()
        }

        temp_file = RETURN_HOME_FILE + ".tmp"

        with open(temp_file, "w") as f:
            json.dump(data, f)

        os.replace(
            temp_file,
            RETURN_HOME_FILE
        )

        print(">>> RETURN TO HOME CANCELLED")

        return jsonify({
            "success": True,
            "return_home": False,
            "message": "RETURN TO HOME CANCELLED"
        })

    except Exception as e:

        print(
            "Cancel Return Home error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print(
        "=========================================="
    )

    print(
        " RESCUE AI REAL-TIME DASHBOARD"
    )

    print(
        "=========================================="
    )

    print(
        "Dashboard: http://0.0.0.0:5000"
    )

    print(
        "Reading AI telemetry"
    )

    print(
        "Reading navigation telemetry"
    )

    print(
        "Return-home control ENABLED"
    )

    print(
        "Press CTRL+C to stop"
    )

    print(
        "=========================================="
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
