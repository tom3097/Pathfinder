SET client_encoding = 'UTF8';

DROP TABLE IF EXISTS locations_test2;

CREATE TABLE locations_test2(id integer);
SELECT AddGeometryColumn('locations_test2', 'geom_coords', 4326, 'POINT', 2);

INSERT INTO locations_test2 VALUES
(630429, ST_SetSRID(ST_MakePoint(16.9238616, 52.9706951), 4326)),
--(538514, ST_SetSRID(ST_MakePoint(16.9080627, 52.9813503), 4326)),
--(639910, ST_SetSRID(ST_MakePoint(17.0053634, 52.9000254), 4326)),
(622323, ST_SetSRID(ST_MakePoint(16.9780635, 52.8851712), 4326)),
(644641, ST_SetSRID(ST_MakePoint(16.9013096, 52.8041031), 4326)),
--(654839, ST_SetSRID(ST_MakePoint(16.8964292, 52.7043855), 4326)),
(61426, ST_SetSRID(ST_MakePoint(16.8752057, 52.6085821), 4326)),
(46958, ST_SetSRID(ST_MakePoint(16.6566569, 52.5971771), 4326)),
--(46089, ST_SetSRID(ST_MakePoint(16.7739217, 52.5520055), 4326)),
(482084, ST_SetSRID(ST_MakePoint(16.8480035, 52.4920835), 4326)),
--(92781, ST_SetSRID(ST_MakePoint(16.9378908, 52.464851), 4326)),
(443464, ST_SetSRID(ST_MakePoint(16.8695636, 52.469511), 4326)),
--(456682, ST_SetSRID(ST_MakePoint(16.851865, 52.4564092), 4326)),
(77478, ST_SetSRID(ST_MakePoint(16.9056409, 52.4289238), 4326)),
(11275, ST_SetSRID(ST_MakePoint(16.8325987, 52.4116322), 4326)),
--(711446, ST_SetSRID(ST_MakePoint(16.9432983, 52.3817153), 4326)),
(394888, ST_SetSRID(ST_MakePoint(16.8576118, 52.3495809), 4326)),
--(507243, ST_SetSRID(ST_MakePoint(16.8198174, 52.3683117), 4326)),
(537244, ST_SetSRID(ST_MakePoint(16.9172196, 52.9949087), 4326)),
(582699, ST_SetSRID(ST_MakePoint(16.7649931, 52.2969), 4326));

ALTER TABLE locations_test2 ADD CONSTRAINT pkey_locations_test2 PRIMARY KEY(id);