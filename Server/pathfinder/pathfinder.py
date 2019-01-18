from postgisdb import PostGisDB
import numpy as np


class Pathfinder(object):
    A = 1.0
    B = 5.0

    def __init__(self, host, port, database, user, password):
        self.routes = []
        self.locations = []
        self.db = PostGisDB(host=host, port=port, database=database,
                            user=user, password=password)
        self.location_ids = []
        self.additional_len = 0
        self.additional_time = 0

    def __print_log(self, start_point_gis, route_gis):
        print('Current point: {}'.format(start_point_gis))
        print('Route length (meters): {}'.format(route_gis.length))
        print('Route time (in hours): {}'.format(route_gis.time))
        print('Additional length: {}'.format(self.additional_len))
        print('Additional time: {}'.format(self.additional_time))
        print('----------------------------------------')

    def __finalize(self, end_point_gis, route_gis):
        print('End point: {}'.format(end_point_gis))
        print('Cannot find points near current location')
        print('----------------------------------------')
        hr_route = self.db.get_human_readable_route(route_gis)
        self.routes.extend(hr_route)
        hr_end = self.db.get_human_readable_point(end_point_gis)
        self.locations.append(hr_end)

    def __proceed(self, start_point_gis, end_point_gis, route_gis):
        self.__print_log(start_point_gis, route_gis)

        # Zapisanie punktu startowego w liscie locations
        hr_start = self.db.get_human_readable_point(start_point_gis)
        self.locations.append(hr_start)
        self.location_ids.append(start_point_gis.p_id)

        # Pobranie z bazy danych punktow (lokalizacji), ktore znajduja sie co najwyzej
        # w odleglosci additional_len od punktu startowego, wraz z tymi odleglosciami
        near_rp_gis, near_rp_dist = self.db.get_locations_near_route(route_gis, self.additional_len)
        assert len(near_rp_gis) == len(near_rp_dist)

        # Jesli zaden punkt nie zostal pobrany, uruchamiana jest funkcja finalizujaca
        # dzialanie algorytmu
        if len(near_rp_gis) == 0:
            self.__finalize(end_point_gis, route_gis)
            return

        # Wyznaczenie odleglosci miedzy kazdym z punktow w liscie near_points_locations
        # a punktem startowym
        start_distances = [self.db.get_points_distance(start_point_gis, near_point_gis)
                           for near_point_gis in near_rp_gis]

        # Odfiltrowanie punktow, ktore zostaly juz odwiedzone przez algorytm lub punktu,
        # ktory jest punktem koncowym
        new_near_rp_gis = []
        new_near_rp_dist = []
        new_start_distances = []
        for rp_gis, rp_dist, start_dist in zip(near_rp_gis, near_rp_dist, start_distances):
            if rp_gis.p_id in self.location_ids or rp_gis.p_id == end_point_gis.p_id:
                continue
            new_near_rp_gis.append(rp_gis)
            new_near_rp_dist.append(rp_dist)
            new_start_distances.append(start_dist)
        assert len(new_near_rp_gis) == len(new_near_rp_dist)
        assert len(new_near_rp_dist) == len(new_start_distances)

        near_rp_gis = np.array(new_near_rp_gis)
        near_rp_dist = np.array(new_near_rp_dist)
        start_distances = np.array(new_start_distances)

        # Jesli odfiltrowane zostaly wszystkie punkty, uruchamiana jest funkcja finalizujaca
        # dzialanie algorytmu
        if len(near_rp_gis) == 0:
            self.__finalize(end_point_gis, route_gis)
            return

        # Obliczenie wspolczynnikow heurystycznych - wspolczynniki alpha i beta
        alpha = route_gis.length / float(self.additional_len) * Pathfinder.A
        beta = self.additional_len / float(route_gis.length) * Pathfinder.B

        # Wyznaczenie kosztu heurystycznego dla kazdego z pozostalych w liscie near_route_locations
        # punktow
        heuristic_cost = near_rp_dist * alpha + start_distances * beta

        # Wybor punktu o najmniejszym koszcie heurystycznym jako nastepnego punktu do odwiedzenia
        loc_candidate_indexes = heuristic_cost.argsort()[0]
        location_gis = near_rp_gis[loc_candidate_indexes]

        # Wyznaczenie trasy od punktu poczatkowego do wybranego punktu
        start_location_route = self.db.get_shortest_route(start_point_gis, location_gis)
        if start_location_route is None:
            self.__finalize(end_point_gis, route_gis)
            return
        # Wyznaczenie trasy od wybranego punktu do punktu koncowego
        location_end_route = self.db.get_shortest_route(location_gis, end_point_gis)
        if location_end_route is None:
            self.__finalize(end_point_gis, route_gis)
            return
        # Obliczenie sumy dlugosci obu tras oraz sumy czasu trwania obu tras
        total_length = start_location_route.length + location_end_route.length
        total_time = start_location_route.time + location_end_route.time

        # Jesli laczna dlugosc tras nie spelnia ograniczen odleglosciowych, uruchamiana jest
        # funnkcja finalizujaca dzialanie algorytmu
        if total_length > route_gis.length + self.additional_len:
            self.__finalize(end_point_gis, route_gis)
            return

        # Jesli laczny czas podrozy nie spelnia ograniczen czasowych, uruchamiana jest
        # funkcja finalizujaca dzialanie algorytmu
        if total_time > route_gis.time + self.additional_time:
            self.__finalize(end_point_gis, route_gis)
            return

        # Uaktualnienie nowych zapasow odleglosciowych i czasowych
        self.additional_len = route_gis.length + self.additional_len - total_length
        self.additional_time = route_gis.time + self.additional_time - total_time

        # Dodanie trasy od punktu startowego do wybranego punktu do listy routes
        hr_route = self.db.get_human_readable_route(start_location_route)
        self.routes.extend(hr_route)

        # Rekurencyjne uruchomienie procedury PROCEED z nowymi argumentami:
        # wybranym punktem, punktem koncowym oraz trasa od wybranego punktu do punktu koncowego
        self.__proceed(location_gis, end_point_gis, location_end_route)

    def run(self, start, end, additional_len, additional_time):
        # Inicjalizacja 'zmiennych globalnych'
        self.locations = []
        self.routes = []
        self.location_ids = []
        self.additional_len = additional_len
        self.additional_time = additional_time

        # Wyznaczenie punktu poczatkowego i koncowego jako najblizszych punktow z bazy
        start_point_gis = self.db.get_nearest_start_point(start['x'], start['y'])
        end_point_gis = self.db.get_nearest_end_point(end['x'], end['y'])

        # Wyznaczenie najkrotszej trasy z punktu poczatkowego do punktu koncowego
        route_gis = self.db.get_shortest_route(start_point_gis, end_point_gis)
        if route_gis is None:
            print('ERROR: Path between given points does not exist')
            return

        # Uruchomienie wlasciwej procedury PROCEED
        self.__proceed(start_point_gis, end_point_gis, route_gis)

    def run_with_first_random(self, start, end, additional_len, additional_time):
        # Inicjalizacja 'zmiennych globalnych'
        self.locations = []
        self.routes = []
        self.location_ids = []
        self.additional_len = additional_len
        self.additional_time = additional_time

        # Wyznaczenie punktu poczatkowego i koncowego jako najblizszych punktow z bazy
        start_point_gis = self.db.get_nearest_start_point(start['x'], start['y'])
        end_point_gis = self.db.get_nearest_end_point(end['x'], end['y'])

        # Wyznaczenie najkrotszej trasy z punktu poczatkowego do punktu koncowego
        route_gis = self.db.get_shortest_route(start_point_gis, end_point_gis)
        if route_gis is None:
            print('ERROR: Path between given points does not exist')
            return

        # Dodanie punktu poczatkowego do listy locations
        hr_start = self.db.get_human_readable_point(start_point_gis)
        self.locations.append(hr_start)
        self.location_ids.append(start_point_gis.p_id)

        # Pobranie z bazy danych punktow (lokalizacji), ktore znajduja sie co najwyzej
        # w odleglosci additional_len / 4 od punktu startowego, wraz z tymi odleglosciami
        near_rp_gis, near_rp_dist = self.db.get_locations_near_route(route_gis, self.additional_len / 4.0)
        assert len(near_rp_gis) == len(near_rp_dist)

        # Jesli zaden punkt nie zostal pobrany, uruchamiana jest funkcja finalizujaca
        # dzialanie algorytmu
        if len(near_rp_gis) == 0:
            self.__finalize(end_point_gis, route_gis)
            return

        # Zmienne pomocnicze
        location_found = False
        max_iterations = 3
        iteration = 0

        total_length = None
        total_time = None
        chosen_location = None
        start_location_route = None
        location_end_route = None

        # Wyznaczenie nowego punktu startowego
        while not location_found and iteration < max_iterations:
            # Wyznaczennie nowego punktu startowego droga losowa
            chosen_location_index = np.random.randint(0, len(near_rp_gis), 1)[0]
            chosen_location = near_rp_gis[chosen_location_index]
            iteration += 1

            # Wyznaczenie trasy od punktu startowego do nowego punktu
            start_location_route = self.db.get_shortest_route(start_point_gis, chosen_location)
            if start_location_route is None:
                continue
            # Wyznaczenie trasy od nowego punktu do punktu koncowego
            location_end_route = self.db.get_shortest_route(chosen_location, end_point_gis)
            if location_end_route is None:
                continue
            # Wyznaczenie sumy odleglosci i czasow dla obi drog
            total_length = start_location_route.length + location_end_route.length
            total_time = start_location_route.time + location_end_route.time

            # Jesli suma odlaelosci lub suma czasow jest wieksza od dopuszczalnej
            # sum, przejdz do nastepnej iteracji
            if total_length > route_gis.length + self.additional_len:
                continue
            if total_time > route_gis.time + self.additional_time:
                continue

            # Nowa likalizacja zostala znaleziona
            location_found = True

        # Jesli nowa lokalizacja nie zostala znaleziona, uruchamiana jest funkcja finalizaujaca
        # dzialanie algorytmu
        if not location_found:
            self.__finalize(end_point_gis, route_gis)
            return

        print('Previous starting location: {}'.format(start_point_gis))
        print('Previous route len: {}'.format(route_gis.length))
        print('Previous route time: {}'.format(route_gis.time))
        print('Previous additional len: {}'.format(additional_len))
        print('Previous additional time: {}'.format(additional_time))
        print('----------------------------------------')

        # Wyznaczanie nowych zapasowych odleglosci i czasow
        new_additional_len = route_gis.length + self.additional_len - total_length
        new_additional_time = route_gis.time + self.additional_time - total_time

        # Dodanie trasy od punktu startowego do wybranej lokacji
        hr_route = self.db.get_human_readable_route(start_location_route)
        self.routes.extend(hr_route)
        self.additional_len = new_additional_len
        self.additional_time = new_additional_time

        print('New starting location: {}'.format(chosen_location))
        print('New route len: {}'.format(location_end_route.length))
        print('New route time: {}'.format(location_end_route.time))
        print('New additional len: {}'.format(new_additional_len))
        print('New additional time: {}'.format(new_additional_time))
        print('----------------------------------------')

        # Uruchomienie wlasciwej procedury znajdowania trasy
        self.__proceed(chosen_location, end_point_gis, location_end_route)
