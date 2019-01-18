from flask import Flask, request, jsonify, send_file
import json
import io
import time
from pathfinder import Pathfinder


app = Flask(__name__, static_url_path='/static')


@app.route('/')
@app.route('/index')
def index():
    return app.send_static_file('index.html')


@app.route('/style')
def style():
    return app.send_static_file('style.css')


@app.route('/script')
def script():
    return app.send_static_file('func.js')


@app.route('/favicon.ico')
def favicon():
    with open('static/favicon.jpg', 'rb') as bites:
        return send_file(io.BytesIO(bites.read()), attachment_filename='favicon.jpeg',
                         mimetype='image/jpg')


@app.route('/find', methods=['POST'])
def find_path():
    if request.method == 'POST':
        pathfinder = Pathfinder(host='localhost', port='5436', database='postgres',
                                user='postgres', password='mysecretpassword')
        data = json.loads(request.data.decode('ascii'))

        start = data['viewparams']['start']
        end = data['viewparams']['end']
        time_limit = data['time']  # hours
        distance_limit = data['distance']  # km

        time_start = time.time()
        # Uruchomienie procedury podstawowej - procedura RUN
        pathfinder.run(start, end, distance_limit * 1000, time_limit)
        time_end = time.time()
        print('Total time (in minutes): {}'.format((time_end - time_start)/60.0))
        print('Number of locations: {}'.format(len(pathfinder.locations)))
        print('Additional len left: {}'.format(pathfinder.additional_len))
        print('Additional time left: {}'.format(pathfinder.additional_time))

        # Sprawdzenie, czy zostalo wykorzystane co najmniej 80% dodatkowych kilometrow
        if pathfinder.additional_len / float(distance_limit * 1000) <= 0.2 or pathfinder.additional_len <= 2000:
            ret = {
                'key_points': pathfinder.locations,
                'route': pathfinder.routes
            }
            return jsonify(ret)

        # Let's try again
        print('Trying one more time')

        locations_backup = pathfinder.locations
        routes_backup = pathfinder.routes

        time_start = time.time()
        # Uruchomienie procedury wyjatkowej - procedura RUN_WITH_FIRST_RANDOM
        pathfinder.run_with_first_random(start, end, distance_limit * 1000, time_limit)
        time_end = time.time()
        print('Total time (in minutes): {}'.format((time_end - time_start)/60.0))
        print('Number of locations: {}'.format(len(pathfinder.locations)))
        print('Additional len left: {}'.format(pathfinder.additional_len))
        print('Additional time left: {}'.format(pathfinder.additional_time))

        if len(pathfinder.locations) > len(locations_backup):
            ret = {
                'key_points': pathfinder.locations,
                'route': pathfinder.routes
            }
            return jsonify(ret)
        else:
            ret = {
                'key_points': locations_backup,
                'route': routes_backup
            }
            return jsonify(ret)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
