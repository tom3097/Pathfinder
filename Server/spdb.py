from flask import Flask, request, jsonify, send_file
import json
import io
import time
from pathfinder import Pathfinder


app = Flask(__name__, static_url_path="/static")


AVG_VEL = 60  # km/h


@app.route("/")
@app.route("/index")
def index():
    return app.send_static_file("index.html")


@app.route("/style")
def style():
    return app.send_static_file("style.css")


@app.route("/script")
def script():
    return app.send_static_file("func.js")


@app.route("/favicon.ico")
def favicon():
    with open("static/favicon.jpg", "rb") as bites:
        return send_file(io.BytesIO(bites.read()), attachment_filename="favicon.jpeg",
                         mimetype="image/jpg")


@app.route("/find", methods = ["POST"])
def find_path():
    if request.method == "POST":
        pathfinder = Pathfinder(host="localhost", port="5436", database="postgres",
                                user="postgres", password="mysecretpassword")
        data = json.loads(request.data.decode("ascii"))

        start = data["viewparams"]["start"]
        end = data["viewparams"]["end"]
        time_limit = data["time"]  # hours
        distance_limit = data["distance"]  # km

        distance = distance_limit if distance_limit < time_limit * AVG_VEL else time_limit * AVG_VEL
        print("Distance limit based on distance: {}".format(distance_limit))
        print("Distance limit based on time: {}".format(time_limit * AVG_VEL))
        print("Chosen distance limit: {}".format(distance))

        time_start = time.time()
        pathfinder.run(start, end, distance * 1000)
        time_end = time.time()
        print("Total time (in minutes): {}".format((time_end - time_start)/60.0))
        print("Number of locations: {}".format(len(pathfinder.locations)))

        ret = {
            "key_points": pathfinder.locations,
            "route": pathfinder.routes
        }

        return jsonify(ret)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
