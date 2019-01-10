from flask import Flask, render_template, request, url_for, jsonify, send_file
import json
import time
import io
from postgisdb import PostGisDB, GisPoint
import numpy as np

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
    with open("static/favicon.jpg", 'rb') as bites:
        return send_file(
                     io.BytesIO(bites.read()),
                     attachment_filename='favicon.jpeg',
                     mimetype='image/jpg'
               )

results = []
routes_list = []


@app.route('/find', methods = ['POST'])
def find_path():
    if request.method == 'POST':
        data = json.loads(request.data.decode('ascii'))

        start = data['viewparams']['start']
        end = data['viewparams']['end']

        run_algorithm(start, end, 2000)

        gen_path = []
        for e in routes_list:
            points = db.get_human_readable_route(e)
            #print(points)
            #print(points[0])
            #print(points[-1])
            gen_path.extend(points)

        # print("GENPATH")
        # print(gen_path)
        # path = gen_path[0]
        # for a in gen_path:
        #     if len(a) > len(path):
        #         path = a
        # print("PATH")
        # print(path)

        ret = { 'key_points': results, 'route': gen_path }

        return jsonify(ret)

db = PostGisDB(host="localhost", port="5433", database="postgres",
                user="postgres", password="")

A = 1.0
B = 10.0
C = 1.0

# liczba rozpatrywanych lokacji
M = 10

def work(start_point_gis, end_point_gis, route_gis, additional_len):
    print("Start point: {}".format(start_point_gis))
    print('Route length: {}'.format(route_gis.length))
    print("Additional length: {}".format(additional_len))
    print("-------------------------------------------------------")
    human_start = db.get_human_readable_point(start_point_gis)
    human_end = db.get_human_readable_point(end_point_gis)
    results.append(human_start)

    near_points_gis, near_route_dists = db.get_locations_near_route(route_gis, additional_len)
    if len(near_points_gis) == 0:
        routes_list.append(route_gis)
        print("Nie ma potencjalnych punktowe near")
        print("End point: {}".format(end_point_gis))
        results.append(human_end)
        return

    # print(near_points_gis)

    start_distances = [db.get_points_distance(start_point_gis, near_point) for near_point in near_points_gis]

    # obliczamy end distance zeby usunac punktu, ktore sa dalej od poczatku
    end_distance = [db.get_points_distance(end_point_gis, near_point) for near_point in near_points_gis]

    start_end_distance = db.get_points_distance(start_point_gis, end_point_gis)

    near_points_gis = np.array(near_points_gis)
    end_distance = np.array(end_distance)
    start_distances = np.array(start_distances)
    near_route_dists = np.array(near_route_dists)

    # skasowanie pierwszego warunku rownowazne z tym, ze trzeba sprawdzac czy dane miasto nie zostalo odwiedzone 2 razy
    correct_indexes = end_distance < start_end_distance
    #correct_indexes = end_distance >= 0.0

    near_points_gis = near_points_gis[correct_indexes]
    start_distances = start_distances[correct_indexes]
    near_route_dists = near_route_dists[correct_indexes]

    if len(near_points_gis) == 0:
        routes_list.append(route_gis)
        print("Po odfiltrowaniu punktow dalszych nie ma near points")
        print("End point: {}".format(end_point_gis))
        results.append(human_end)
        return

    # print(start_distances)

    alpha = route_gis.length / float(additional_len) * A
    beta = additional_len / float(route_gis.length) * B

    # start_distances = np.array(start_distances)

    assert len(near_route_dists) == len(start_distances)

    heuristic_cost = near_route_dists * alpha + start_distances * beta

    # print(heuristic_cost.shape[0])

    chosen_indexes = heuristic_cost.argsort()[:M]

    # print(chosen_indexes)

    chosen_points = near_points_gis[chosen_indexes]
    chosen_points_heuristics = heuristic_cost[chosen_indexes]

    #print(chosen_points)
    #print(heuristic_cost[chosen_indexes])

    routes_to_point = []
    routes_from_point = []
    total_lengths = []
    routes_from_point_lengths = []

    for ch_point in chosen_points:
        start_point_route = db.get_shortest_route(start_point_gis, ch_point)
        if start_point_route is None:
            continue
        point_end_route = db.get_shortest_route(ch_point, end_point_gis)
        if point_end_route is None:
            continue
        length = start_point_route.length + point_end_route.length

        routes_to_point.append(start_point_route)
        routes_from_point.append(point_end_route)
        total_lengths.append(length)
        routes_from_point_lengths.append(point_end_route.length)

    routes_to_point = np.array(routes_to_point)
    routes_from_point = np.array(routes_from_point)
    if len(routes_from_point) == 0:
        routes_list.append(route_gis)
        print("Dijsktra nie znalazl polaczen")
        print("End point: {}".format(end_point_gis))
        results.append(human_end)
        return

    total_lengths = np.array(total_lengths)
    routes_from_point_lengths = np.array(routes_from_point_lengths)

    correct_indexes = total_lengths <= route_gis.length + additional_len

    routes_to_point = routes_to_point[correct_indexes]
    routes_from_point = routes_from_point[correct_indexes]
    total_lengths = total_lengths[correct_indexes]
    chosen_points_heuristics = chosen_points_heuristics[correct_indexes]

    diff_dist = routes_from_point_lengths - route_gis.length
    diff_dist = np.max(diff_dist, 0)
    chosen_points_heuristics = chosen_points_heuristics + C * diff_dist

    odw = 1.0 / chosen_points_heuristics
    af = odw / np.sum(odw)

    #print(total_lengths)
    #print(af)

    if len(routes_from_point) == 0:
        routes_list.append(route_gis)
        print("Brak kandydatow, koniec algorytmu")
        print("End point: {}".format(end_point_gis))
        results.append(human_end)
        return

    mid_point_idx = np.random.choice(len(total_lengths), 1, p=af)[0]
    #print("Mid point: {}".format(mid_point_idx))

    mid_point = chosen_points[mid_point_idx]

    #print("Mid point")
    #print(mid_point)

    mid_point_len = total_lengths[mid_point_idx]

    add_len_2 = route_gis.length + additional_len - mid_point_len
    route_to_mid_point = routes_to_point[mid_point_idx]
    routes_list.append(route_to_mid_point)
    new_route = routes_from_point[mid_point_idx]

    work(mid_point, end_point_gis, new_route, add_len_2)

def run_algorithm(start, end, additional_len):
    global results
    global routes_list
    results = []
    routes_list = []

    start_point_gis = db.get_nearest_start_point(start['x'], start['y'])
    end_point_gis = db.get_nearest_end_point(end['x'], end['y'])

    route_gis = db.get_shortest_route(start_point_gis, end_point_gis)

    if route_gis is None:
        print("Droga pomiedzy zadanymi punktami nie istnieje w ramach granicy Polski")
        exit()

    work(start_point_gis, end_point_gis, route_gis, additional_len)

    print(results)

app.run(port=5000, debug=True)


#
# if __name__ == '__main__':
#     start = {
#         'x': 22.0,
#         'y': 51.0
#     }
#
#     end = {
#         'x': 20.0,
#         'y': 50.0
#     }
#     run_algorithm(start, end, 10000)
