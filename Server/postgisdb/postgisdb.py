import psycopg2
import parse


class GisPoint(object):
    """ Represents a postgis point.

    """
    def __init__(self, p_id, binary):
        self.p_id = p_id
        self.binary = binary

    def __str__(self):
        return 'id={}, binary={}'.format(self.p_id, self.binary)


class GisRoute(object):
    """ Represents a postgis route.

    """
    def __init__(self, binary, length):
        self.binary = binary
        self.length = length

    def __str__(self):
        return 'binary={}, length={}'.format(self.binary, self.length)


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
        query = "SELECT t.source, ST_SetSrid(ST_MakePoint(t.x1, t.y1), 4326) " \
                "FROM (SELECT source, x1, y1 FROM hh_2po_4pgr " \
                "ORDER BY sqrt((x1 - {})*(x1 - {}) + (y1 - {})*(y1 - {}))" \
                "LIMIT 1) as t;".format(x, x, y, y)

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()

        return GisPoint(*row)

    def get_nearest_end_point(self, x, y):
        """ Gets nearest target for the given point.

        """
        query = "SELECT t.target, ST_SetSrid(ST_MakePoint(t.x2, t.y2), 4326) " \
                "FROM (SELECT target, x2, y2 FROM hh_2po_4pgr " \
                "ORDER BY sqrt((x2 - {})*(x2 - {}) + (y2 - {})*(y2 - {}))" \
                "LIMIT 1) as t;".format(x, x, y, y)

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()

        return GisPoint(*row)

    def get_shortest_route(self, point_1, point_2):
        """ Gets shortest path between two points (dijkstra, in meters).

        """
        dijkstra_query = "SELECT ST_Union(ARRAY(SELECT geom_way FROM pgr_dijkstra('" \
                         "SELECT id, source, target, km as cost FROM hh_2po_4pgr', " \
                         "{}, {}, false) AS route1 LEFT JOIN hh_2po_4pgr as route2 " \
                         "ON (route1.edge = route2.id) ORDER BY seq));"\
            .format(point_1.p_id, point_2.p_id)

        curr = self.connection.cursor()
        curr.execute(dijkstra_query)
        route = curr.fetchone()[0]

        if route is None:
            return None

        length_query = "SELECT ST_Length('{}'::geography);".format(route)

        curr.execute(length_query)
        route_len = curr.fetchone()[0]

        return GisRoute(route, route_len)

    def get_locations_near_route(self, route, max_len):
        """ Gets locations within max_len meters from the route.

        """
        query = "SELECT * FROM (SELECT id, geom_coords, ST_Distance('{}'::geography, " \
                "geom_coords::geography) AS dist FROM locations) AS " \
                "t WHERE t.dist < {}".format(route.binary, max_len)

        curr = self.connection.cursor()
        curr.execute(query)

        rows = curr.fetchall()

        points_gis = [GisPoint(l[0], l[1]) for l in rows]
        route_distances = [l[2] for l in rows]

        return points_gis, route_distances

    def get_points_distance(self, point_1, point_2):
        """ Gets distance between two points (in meters).

        """
        query = "SELECT ST_Distance('{}'::geography, '{}'::geography);"\
            .format(point_1.binary, point_2.binary)

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()

        return row[0]

    def get_human_readable_point(self, point):
        """ Gets human readable representation for the given point.

        """
        query = "SELECT ST_AsText('{}');".format(point.binary)
        format_string = 'POINT({:f} {:f})'

        curr = self.connection.cursor()
        curr.execute(query)

        row = parse.parse(format_string, curr.fetchone()[0])

        coords = {
            'x': row[0],
            'y': row[1]
        }

        return coords

    def get_human_readable_route(self, route):
        """ Gets human readable representation for the given route.

        """
        query = "SELECT ST_AsText('{}');".format(route.binary)
        format_string = '(\"<{:d},{:d}>\",{})'
        format_string2 = 'POINT({:f} {:f})'

        curr = self.connection.cursor()
        curr.execute(query)

        row = curr.fetchone()[0]

        query2 = "SELECT ST_DumpPoints('{}')".format(row)
        curr.execute(query2)

        row = curr.fetchall()

        points = []

        lines = {}

        for r in row:
            #print(r[0])
            data_line = r[0]
            data_line = data_line.replace('{', '<').replace('}', '>')
            #print(data_line)

            data = parse.parse(format_string, data_line)
            #print(data)
            try:
                # przy takim case leci error: (<1>,01010000008CBE823463773140AFD7AA1386564A40) = data_line
                # generalnie jest to 1 punkt, ktory nie wyznacza (nie definiuje) trasy, wiec wydaje mi sie
                # ze mozna go pominac przy rysowaniu
                line_nr = data[0]
            except Exception:
                print('!!!!!!!!!!!!!!!!!!EXCEPTION: otrzymano multiline skladajace sie tylko z jednego punktyu!!!!!!!!!!!!!!!!!!')
                print(data)
                print(data_line)
                continue
            if line_nr not  in lines:
                lines[line_nr] = []
            gis_point = data[2]
            query = "SELECT ST_AsText('{}');".format(gis_point)
            curr.execute(query)
            pp = parse.parse(format_string2, curr.fetchone()[0])
            #print(pp)
            coords = {
                'x': pp[0],
                'y': pp[1]
            }
            lines[line_nr].append(coords)
            #print(coords)

        #print(points)

        for key, val in lines.iteritems():
            #print(val)
            points.append(val)

        return points




        #print(row)

    # def get_points_distance(self, point_1, point_2):
    #     """ Gets distance between two points (in meters).
    #
    #     """
    #     query = "SELECT ST_Distance('SRID=4326;POINT({} {})'::geography, " \
    #             "'SRID=4326;POINT({} {})'::geography);"\
    #         .format(point_1.x, point_1.y, point_2.x, point_2.y)
    #
    #     curr = self.connection.cursor()
    #     curr.execute(query)
    #
    #     row = curr.fetchone()
    #
    #     return row[0]

    # def get_route_point_distance(self, route, point):
    #     """ Gets distance between route and point (in meters).
    #
    #     """
    #     query = "SELECT ST_Distance('{}'::geography, 'SRID=4326;POINT" \
    #             "({} {})'::geography)".format(route, point.x, point.y)
    #
    #     curr = self.connection.cursor()
    #     curr.execute(query)
    #
    #     row = curr.fetchone()
    #
    #     return row[0]


    # def get_point_db_point_distance(self, point, db_point):
    #     query = "SELECT ST_Distance('SRID=4326;POINT({} {})'::geography, " \
    #             "'SRID=4326;POINT({} {})'::geography);"\
    #         .format(point_1.x, point_1.y, point_2.x, point_2.y)
    #
    #     curr = self.connection.cursor()
    #     curr.execute(query)
    #
    #     row = curr.fetchone()
    #
    #     return row[0]


def _test_db_queries():
    db = PostGisDB(host="localhost", port="5433", database="postgres",
                   user="postgres", password="mysecretpassword")

    point_A_gis = db.get_nearest_start_point(22.0, 51.0)
    point_B_gis = db.get_nearest_end_point(20.0, 50.0)
    print('Point A: {}'.format(point_A_gis))
    print('Point B: {}'.format(point_B_gis))

    distance_A_B = db.get_points_distance(point_A_gis, point_B_gis)
    print('Distance A-B: {}'.format(distance_A_B))

    route_gis = db.get_shortest_route(point_A_gis, point_B_gis)
    print('Shortest route: {}'.format(route_gis))
    #
    # distance_route_A = db.get_route_point_distance(route, point_A)
    # print('Distance route-A: {}'.format(distance_route_A))
    #
    near_loc_points_gis, near_loc_route_dist = db.get_locations_near_route(route_gis, 1000)
    print('Locations near route:')
    for p, d in zip(near_loc_points_gis, near_loc_route_dist):
        print('Point: {}, distance: {}'.format(p, d))

    human_readable = db.get_human_readable_point(point_A_gis)
    print(human_readable)

    db.get_human_readable_route(route_gis)

if __name__ == '__main__':
    _test_db_queries()
