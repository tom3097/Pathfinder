import psycopg2
import parse
from typing import Optional, Tuple, List, Dict


class GisPoint(object):
    def __init__(self, p_id: int, binary: str):
        self.p_id = p_id
        self.binary = binary

    def __str__(self) -> str:
        return 'id={}, binary={}'.format(self.p_id, self.binary)


class GisRoute(object):
    def __init__(self, binary: str, length: int):
        self.binary = binary
        self.length = length

    def __str__(self) -> str:
        return 'binary={}, length={}'.format(self.binary, self.length)


class PostGisDB(object):
    NEAREST_START_POINT_QUERY = "SELECT t.source, ST_SetSrid(ST_MakePoint(t.x1, t.y1), " \
                                "4326) FROM (SELECT source, x1, y1 FROM hh_2po_4pgr " \
                                "ORDER BY sqrt((x1 - {})*(x1 - {}) + (y1 - {})*(y1 - {}))" \
                                "LIMIT 1) as t;"
    NEAREST_END_POINT_QUERY = "SELECT t.target, ST_SetSrid(ST_MakePoint(t.x2, t.y2), " \
                              "4326) FROM (SELECT target, x2, y2 FROM hh_2po_4pgr " \
                              "ORDER BY sqrt((x2 - {})*(x2 - {}) + (y2 - {})*(y2 - {}))" \
                              "LIMIT 1) as t;"
    SHORTEST_ROUTE_QUERY = "SELECT ST_Union(ARRAY(SELECT geom_way FROM pgr_dijkstra('" \
                           "SELECT id, source, target, km as cost FROM hh_2po_4pgr', " \
                           "{}, {}, false) AS route1 LEFT JOIN hh_2po_4pgr as route2 " \
                           "ON (route1.edge = route2.id) ORDER BY seq));"
    ROUTE_LENGTH_QUERY = "SELECT ST_Length('{}'::geography);"
    LOCATIONS_NEAR_ROUTE_QUERY = "SELECT * FROM (SELECT id, geom_coords, ST_Distance" \
                                 "('{}'::geography, geom_coords::geography) AS dist FROM " \
                                 "locations) AS t WHERE t.dist < {}"
    POINTS_DISTANCE_QUERY = "SELECT ST_Distance('{}'::geography, '{}'::geography);"
    HUMAN_READABLE_QUERY = "SELECT ST_AsText('{}');"
    DUMP_POINTS_QUERY = "SELECT ST_DumpPoints('{}');"

    FORMAT_STRING_POINT = "POINT({:f} {:f})"
    FORMAT_STRING_DUMP_POINTS = "(\"<{:d},{:d}>\",{})"

    def __init__(self, host: str, port: str, database: str, user: str, password: str):
        self.connection = psycopg2.connect(host=host, port=port, database=database,
                                           user=user, password=password)

    def close(self):
        self.connection.close()

    def get_nearest_start_point(self, x: float, y: float) -> GisPoint:
        curr = self.connection.cursor()
        curr.execute(PostGisDB.NEAREST_START_POINT_QUERY.format(x, x, y, y))
        row = curr.fetchone()

        return GisPoint(*row)

    def get_nearest_end_point(self, x: float, y: float) -> GisPoint:
        curr = self.connection.cursor()
        curr.execute(PostGisDB.NEAREST_END_POINT_QUERY.format(x, x, y, y))
        row = curr.fetchone()

        return GisPoint(*row)

    def get_shortest_route(self, point_1: GisPoint, point_2: GisPoint) -> Optional[GisRoute]:
        curr = self.connection.cursor()
        curr.execute(PostGisDB.SHORTEST_ROUTE_QUERY.format(point_1.p_id, point_2.p_id))
        route = curr.fetchone()[0]
        if route is None:
            return None

        curr.execute(PostGisDB.ROUTE_LENGTH_QUERY.format(route))
        route_len = curr.fetchone()[0]

        return GisRoute(route, route_len)

    def get_locations_near_route(self, route: GisRoute, max_len: float) -> Tuple[List[GisPoint], List[float]]:
        curr = self.connection.cursor()
        curr.execute(PostGisDB.LOCATIONS_NEAR_ROUTE_QUERY.format(route.binary, max_len))
        rows = curr.fetchall()

        points_gis = [GisPoint(l[0], l[1]) for l in rows]
        route_distances = [l[2] for l in rows]

        return points_gis, route_distances

    def get_points_distance(self, point_1: GisPoint, point_2: GisPoint) -> float:
        curr = self.connection.cursor()
        curr.execute(PostGisDB.POINTS_DISTANCE_QUERY.format(point_1.binary, point_2.binary))
        row = curr.fetchone()

        return row[0]

    def get_human_readable_point(self, point: GisPoint) -> Dict[str, float]:
        curr = self.connection.cursor()
        curr.execute(PostGisDB.HUMAN_READABLE_QUERY.format(point.binary))
        row = parse.parse(PostGisDB.FORMAT_STRING_POINT, curr.fetchone()[0])
        coords = {
            'x': row[0],
            'y': row[1]
        }

        return coords

    def get_human_readable_route(self, route: GisRoute) -> List[List[Dict[str, float]]]:
        curr = self.connection.cursor()
        curr.execute(PostGisDB.HUMAN_READABLE_QUERY.format(route.binary))
        row = curr.fetchone()[0]

        curr.execute(PostGisDB.DUMP_POINTS_QUERY.format(row))
        rows = curr.fetchall()

        lines: Dict[int, List[Dict[str, float]]] = {}
        for r in rows:
            data_line = r[0].replace('{', '<').replace('}', '>')
            data = parse.parse(PostGisDB.FORMAT_STRING_DUMP_POINTS, data_line)
            if data is None:
                continue

            line_id = data[0]
            if line_id not in lines:
                lines[line_id] = []

            binary_point = data[2]
            curr.execute(PostGisDB.HUMAN_READABLE_QUERY.format(binary_point))
            hr_point = parse.parse(PostGisDB.FORMAT_STRING_POINT, curr.fetchone()[0])
            coords = {
                'x': hr_point[0],
                'y': hr_point[1]
            }
            lines[line_id].append(coords)

        points = []
        for key, val in lines.items():
            points.append(val)

        return points


def _test_db_queries():
    db = PostGisDB(host="localhost", port="5436", database="postgres",
                   user="postgres", password="mysecretpassword")

    point_a_gis = db.get_nearest_start_point(22.0, 51.0)
    print("Point A: {}".format(point_a_gis))

    point_b_gis = db.get_nearest_end_point(20.0, 50.0)
    print("Point B: {}".format(point_b_gis))

    route_gis = db.get_shortest_route(point_a_gis, point_b_gis)
    print("Shortest route: {}".format(route_gis))

    near_loc_points_gis, near_loc_route_dist = db.get_locations_near_route(route_gis, 1000.5)
    print("Locations near route:")
    for p, d in zip(near_loc_points_gis, near_loc_route_dist):
        print("Point: {}, distance: {}".format(p, d))

    distance_a_b = db.get_points_distance(point_a_gis, point_b_gis)
    print("Distance A-B: {}".format(distance_a_b))

    human_readable_point = db.get_human_readable_point(point_a_gis)
    print("Human readable point: {}".format(human_readable_point))

    human_readable_route = db.get_human_readable_route(route_gis)
    print("Human readable route: {}".format(human_readable_route))


if __name__ == "__main__":
    _test_db_queries()
