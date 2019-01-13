from postgisdb import PostGisDB, GisPoint, GisRoute
import numpy as np
from typing import List, Dict


class Pathfinder(object):
    A = 1.0
    B = 10.0
    C = 1.0
    M = 1

    def __init__(self, host: str, port: str, database: str, user: str, password: str):
        self.routes: List[List[Dict[str, float]]] = []
        self.locations: List[Dict[str, float]] = []
        self.db = PostGisDB(host=host, port=port, database=database,
                            user=user, password=password)

    def __proceed(self, start_point_gis: GisPoint, end_point_gis: GisPoint, route_gis: GisRoute,
                  additional_len: float):
        print("Current point: {}".format(start_point_gis))
        print("Route length (meters): {}".format(route_gis.length))
        print("Additional length: {}".format(additional_len))
        print("---------------------------------------------------")

        hr_start = self.db.get_human_readable_point(start_point_gis)
        self.locations.append(hr_start)

        near_rp_gis, near_rp_dist = self.db.get_locations_near_route(route_gis, additional_len)
        assert len(near_rp_gis) == len(near_rp_dist)

        if len(near_rp_gis) == 0:
            print("End point: {}".format(end_point_gis))
            print("Cannot find points near current location")
            hr_route = self.db.get_human_readable_route(route_gis)
            self.routes.extend(hr_route)
            hr_end = self.db.get_human_readable_point(end_point_gis)
            self.locations.append(hr_end)
            return

        start_distances = [self.db.get_points_distance(start_point_gis, near_point_gis)
                           for near_point_gis in near_rp_gis]
        end_distances = [self.db.get_points_distance(end_point_gis, near_point_gis)
                         for near_point_gis in near_rp_gis]
        start_end_distance = self.db.get_points_distance(start_point_gis, end_point_gis)

        near_rp_gis = np.array(near_rp_gis)
        near_rp_dist = np.array(near_rp_dist)
        start_distances = np.array(start_distances)
        end_distances = np.array(end_distances)

        correct_indexes = end_distances < start_end_distance  # type: ignore

        near_rp_gis = near_rp_gis[correct_indexes]
        near_rp_dist = near_rp_dist[correct_indexes]
        start_distances = start_distances[correct_indexes]

        assert len(near_rp_gis) == len(near_rp_dist)
        assert len(near_rp_dist) == len(start_distances)

        if len(near_rp_gis) == 0:
            print("End point: {}".format(end_point_gis))
            print("Cannot find location that decreases length to the end point")
            hr_route = self.db.get_human_readable_route(route_gis)
            self.routes.extend(hr_route)
            hr_end = self.db.get_human_readable_point(end_point_gis)
            self.locations.append(hr_end)
            return

        alpha = route_gis.length / float(additional_len) * Pathfinder.A
        beta = additional_len / float(route_gis.length) * Pathfinder.B

        heuristic_cost = near_rp_dist * alpha + start_distances * beta  # type: ignore
        loc_candidate_indexes = heuristic_cost.argsort()[:Pathfinder.M]

        loc_candidate_points_gis = near_rp_gis[loc_candidate_indexes]
        loc_candidates_heuristic_cost = heuristic_cost[loc_candidate_indexes]

        assert len(loc_candidate_points_gis) == len(loc_candidates_heuristic_cost)

        routes_to_location = []
        routes_from_location = []
        total_lengths = []
        routes_from_location_lengths = []
        lc_heuristic_cost = []
        lc_points_gis = []

        for location, cost in zip(loc_candidate_points_gis, loc_candidates_heuristic_cost):
            start_location_route = self.db.get_shortest_route(start_point_gis, location)
            if start_location_route is None:
                continue
            location_end_route = self.db.get_shortest_route(location, end_point_gis)
            if location_end_route is None:
                continue
            length = start_location_route.length + location_end_route.length

            routes_to_location.append(start_location_route)
            routes_from_location.append(location_end_route)
            total_lengths.append(length)
            routes_from_location_lengths.append(location_end_route.length)
            lc_heuristic_cost.append(cost)
            lc_points_gis.append(location)

        routes_to_location = np.array(routes_to_location)
        routes_from_location = np.array(routes_from_location)
        total_lengths = np.array(total_lengths)
        routes_from_location_lengths = np.array(routes_from_location_lengths)
        lc_heuristic_cost = np.array(lc_heuristic_cost)
        lc_points_gis = np.array(lc_points_gis)

        assert len(routes_to_location) == len(routes_from_location)
        assert len(routes_from_location) == len(total_lengths)
        assert len(total_lengths) == len(routes_from_location_lengths)
        assert len(routes_from_location_lengths) == len(lc_heuristic_cost)
        assert len(lc_heuristic_cost) == len(lc_points_gis)

        if len(routes_from_location) == 0:
            print("End point: {}".format(end_point_gis))
            print("Cannot find any path using Dijkstra")
            hr_route = self.db.get_human_readable_route(route_gis)
            self.routes.extend(hr_route)
            hr_end = self.db.get_human_readable_point(end_point_gis)
            self.locations.append(hr_end)
            return

        correct_indexes = total_lengths <= route_gis.length + additional_len  # type: ignore

        routes_to_location = routes_to_location[correct_indexes]
        routes_from_location = routes_from_location[correct_indexes]
        total_lengths = total_lengths[correct_indexes]
        routes_from_location_lengths = routes_from_location_lengths[correct_indexes]
        lc_heuristic_cost = lc_heuristic_cost[correct_indexes]
        lc_points_gis = lc_points_gis[correct_indexes]

        assert len(routes_to_location) == len(routes_from_location)
        assert len(routes_from_location) == len(total_lengths)
        assert len(total_lengths) == len(routes_from_location_lengths)
        assert len(routes_from_location_lengths) == len(lc_heuristic_cost)
        assert len(lc_heuristic_cost) == len(lc_points_gis)

        if len(routes_from_location) == 0:
            print("End point: {}".format(end_point_gis))
            print("Cannot find locations close enough")
            hr_route = self.db.get_human_readable_route(route_gis)
            self.routes.extend(hr_route)
            hr_end = self.db.get_human_readable_point(end_point_gis)
            self.locations.append(hr_end)
            return

        penalty_cost = routes_from_location_lengths - route_gis.length  # type: ignore
        penalty_cost[penalty_cost < 0] = 0  # type: ignore
        routes_heuristic_cost = lc_heuristic_cost + Pathfinder.C * penalty_cost  # type: ignore

        inverse_cost = 1.0 / routes_heuristic_cost
        probabilities = inverse_cost / np.sum(inverse_cost)

        chosen_location_index = np.random.choice(len(lc_points_gis), 1, p=probabilities)[0]
        chosen_location = lc_points_gis[chosen_location_index]

        new_additional_len = route_gis.length + additional_len - total_lengths[chosen_location_index]
        route_to_chosen_location = routes_to_location[chosen_location_index]
        hr_route = self.db.get_human_readable_route(route_to_chosen_location)
        self.routes.extend(hr_route)
        new_route_gis = routes_from_location[chosen_location_index]

        self.__proceed(chosen_location, end_point_gis, new_route_gis, new_additional_len)

    def run(self, start: Dict[str, float], end: Dict[str, float], additional_len: float):
        self.locations = []
        self.routes = []

        start_point_gis = self.db.get_nearest_start_point(start['x'], start['y'])
        end_point_gis = self.db.get_nearest_end_point(end['x'], end['y'])

        route_gis = self.db.get_shortest_route(start_point_gis, end_point_gis)
        if route_gis is None:
            print("Path between points does not exist")
            return

        self.__proceed(start_point_gis, end_point_gis, route_gis, additional_len)
