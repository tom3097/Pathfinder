import psycopg2


class Point(object):
    """ Represents a point.

    """
    def __init__(self, p_id, x, y):
        self.p_id = p_id
        self.x = x
        self.y = y

    def __str__(self):
        return 'Id={}, x={}, y={}'.format(self.p_id, self.x, self.y)


class PostGisDB(object):
    """ Wrapper for PostGis database.

    """
    def __init__(self, host, port, database, user, password):
        self.connection = psycopg2.connect(host=host, port=port, database=database,
                                           user=user, password=password)

    def close(self):
        """ Closes database connection.

        """
        self.connection.close()

    def get_nearest_start_point(self, x, y):
        """ Gets nearest source for the given point.

        """
        query = "SELECT source, x1, y1 FROM hh_2po_4pgr " \
                "ORDER BY sqrt((x1 - {})*(x1 - {}) + (y1 - {})*(y1 - {}))" \
                "LIMIT 1;".format(x, x, y, y)

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()

        return Point(*row)

    def get_nearest_end_point(self, x, y):
        """ Gets nearest target for the given point.

        """
        query = "SELECT target, x2, y2 FROM hh_2po_4pgr " \
                "ORDER BY sqrt((x2 - {})*(x2 - {}) + (y2 - {})*(y2 - {}))" \
                "LIMIT 1;".format(x, x, y, y)

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()

        return Point(*row)

    def get_shortest_route(self, point_1, point_2):
        """ Gets shortest path between two points (dijkstra, in meters).

        """
        dijkstra_query = "SELECT ST_Union(ARRAY(SELECT geom_way FROM pgr_dijkstra('" \
                "SELECT id, source, target, km as cost FROM hh_2po_4pgr', " \
                "183959, 347, false) AS route1 LEFT JOIN hh_2po_4pgr as route2 " \
                "ON (route1.edge = route2.id) ORDER BY seq));"\
            .format(point_1.p_id, point_2.p_id)

        curr = self.connection.cursor()
        curr.execute(dijkstra_query)
        route = curr.fetchone()[0]

        length_query = "SELECT ST_Length('{}'::geography);".format(route)

        curr.execute(length_query)
        route_len = curr.fetchone()[0]

        return route, route_len

    def get_points_distance(self, point_1, point_2):
        """ Gets distance between two points (in meters).

        """
        query = "SELECT ST_Distance('SRID=4326;POINT({} {})'::geography, " \
                "'SRID=4326;POINT({} {})'::geography);"\
            .format(point_1.x, point_1.y, point_2.x, point_2.y)

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()

        return row[0]

    def get_route_point_distance(self, route, point):
        """ Gets distance between route and point (in meters).

        """
        query = "SELECT ST_Distance('{}'::geography, 'SRID=4326;POINT" \
                "({} {})'::geography)".format(route, point.x, point.y)

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()

        return row[0]


if __name__ == '__main__':
    db = PostGisDB(host="localhost", port="5433", database="postgres",
                   user="postgres", password="mysecretpassword")

    point_A = db.get_nearest_start_point(22.0, 51.0)
    point_B = db.get_nearest_end_point(20.0, 50.0)
    print('Point A: {}'.format(point_A))
    print('Point B: {}'.format(point_B))

    distance_A_B = db.get_points_distance(point_A, point_B)
    print('Distance A-B: {}'.format(distance_A_B))

    route, route_len = db.get_shortest_route(point_A, point_B)
    print('Shortest route: {}'.format(route))
    print('Shortest route length: {}'.format(route_len))

    distance_route_A = db.get_route_point_distance(route, point_A)
    print('Distance route-A: {}'.format(distance_route_A))
