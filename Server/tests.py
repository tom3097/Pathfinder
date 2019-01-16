import psycopg2
import json

SELECT_POINTS_TEST1 = "SELECT * FROM locations_test1;"
SELECT_POINTS_TEST2 = "SELECT * FROM locations_test2;"
SELECT_POINTS_TEST3 = "SELECT * FROM locations_test3;"

SHORTEST_ROUTE_QUERY = "SELECT agg_cost FROM pgr_dijkstra(" \
                       "'SELECT id, source, target, km as cost FROM hh_2po_4pgr', " \
                       "{}, {}, false) AS route1 LEFT JOIN hh_2po_4pgr as route2 " \
                       "ON (route1.edge = route2.id) ORDER BY seq;"

connection = None

shortest_len = 0    # km
distance = 250       # km   # 30, 100, 250
time = 2            # hours

def queryPoints(query):
    curr = connection.cursor()
    curr.execute(query)
    points = curr.fetchall()
    return [point[0] for point in points]

def computePathsLen(points):
    curr = connection.cursor()
    curr.execute(SHORTEST_ROUTE_QUERY.format(points[0], points[-1]))
    shortest_len = curr.fetchall()[-1][0]
    print("==================================================")
    print("A -> B : {}".format(shortest_len))
    print("==================================================")

    paths = {}
    with open('./tests/test3.json') as f:
        paths = json.loads(f.read())

    print(paths)

    # for i in range(0, len(points)):
    #     pointA = points[i]
    #
    #     paths.update({pointA : {}})
    #
    #     rest_points = list(points)
    #     del rest_points[i]
    #     for pointB in rest_points:
    #         curr = connection.cursor()
    #         curr.execute(SHORTEST_ROUTE_QUERY.format(pointA, pointB))
    #         res = curr.fetchall()
    #         length = 0
    #         if len(res) == 0:
    #             length = distance * distance
    #         else:
    #             length = res[-1][0]
    #         paths[pointA].update({pointB : length})
    #
    #     print("{}: {}".format(pointA, paths[pointA]))
    print("==================================================")

    # print(json.dumps(paths, ensure_ascii=False))

    return paths

def buildGraph(points):
    graph = {}
    for i in range(0, len(points)):
        pointA = points[i]

        graph.update({pointA : set()})

        rest_points = list(points)
        del rest_points[i]
        for pointB in rest_points:
            graph[pointA].add(pointB)

    return graph

def pathLen(path, costs):
    length = 0
    for i in range(0, len(path)):
        if i + 1 < len(path):
            length += costs[str(path[i])][str(path[i+1])]
        else:
            return length

def dfs_paths(graph, start, goal, costs):
    stack = [(start, [start])]
    while stack:
        (vertex, path) = stack.pop()
        for next in graph[vertex]: # - set(path):
            if pathLen(path + [next], costs) > (shortest_len + distance):
                continue

            if next == goal:
                yield path + [next]
            else:
                stack.append((next, path + [next]))

def test(points):
    print("==================================================")
    print(points)
    graph = buildGraph(points)
    print("==================================================")
    print(graph)
    costs = computePathsLen(points)
    paths = list(dfs_paths(graph, points[0], points[-1], costs))

    longest_path = []
    max_length = 0
    for path in paths:
        length = 0
        for i in range(0, len(path)):
            if i + 1 < len(path):
                length += costs[str(path[i])][str(path[i+1])]
            else:
                break
        print("==================================================")
        print("{} - {}".format(path, length))
        if max_length < length:
            max_length = length
            longest_path = list(path)
    print("==================================================")
    print("{} - {}".format(longest_path, max_length))
    print("==================================================")

if __name__ == '__main__':
    # connection = psycopg2.connect(host='localhost', port=5432, database='osm_pgr',
    #                                    user='postgres', password='123abc')
    connection = psycopg2.connect(host="localhost", port="5436", database="postgres",
                                       user="postgres", password="mysecretpassword")
    # test(queryPoints(SELECT_POINTS_TEST1))
    # test(queryPoints(SELECT_POINTS_TEST2))
    test(queryPoints(SELECT_POINTS_TEST3))
    connection.close()
