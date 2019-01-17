SET client_encoding = 'UTF8';

DROP TABLE IF EXISTS locations_test3;

CREATE TABLE locations_test3(id integer);
SELECT AddGeometryColumn('locations_test3', 'geom_coords', 4326, 'POINT', 2);

INSERT INTO locations_test3 VALUES
(169682, ST_SetSRID(ST_MakePoint(18.5996956, 54.337689), 4326)),
--(88457, ST_SetSRID(ST_MakePoint(18.6726718, 54.0377488), 4326)),
(1015089, ST_SetSRID(ST_MakePoint(18.6277443, 54.2680589), 4326)),
--(692915, ST_SetSRID(ST_MakePoint(18.801467, 54.0799229), 4326)),
--(652532, ST_SetSRID(ST_MakePoint(19.1327084, 54.1958512), 4326)),
(234295, ST_SetSRID(ST_MakePoint(19.0684372, 54.0381612), 4326)),
--(680791, ST_SetSRID(ST_MakePoint(18.767903, 53.9270651), 4326)),
(308063, ST_SetSRID(ST_MakePoint(18.9949245, 53.8361345), 4326)),
--(855822, ST_SetSRID(ST_MakePoint(18.8660499, 53.6579778), 4326)),
(230801, ST_SetSRID(ST_MakePoint(19.5673876, 53.5864937), 4326)),
(610434, ST_SetSRID(ST_MakePoint(18.9556811, 53.2624773), 4326)),
--(636644, ST_SetSRID(ST_MakePoint(20.0930517, 53.0818907), 4326)),
(629032, ST_SetSRID(ST_MakePoint(19.5579661, 52.7114326), 4326)),
--(473913, ST_SetSRID(ST_MakePoint(20.3137073, 52.7518982), 4326)),
(767920, ST_SetSRID(ST_MakePoint(20.9400828, 52.492739), 4326)),
(447421, ST_SetSRID(ST_MakePoint(19.8095108, 53.2707444), 4326)),
--(144582, ST_SetSRID(ST_MakePoint(18.9401026, 53.3827551), 4326)),
(1002174, ST_SetSRID(ST_MakePoint(20.3538058, 53.124186), 4326)),
(40563, ST_SetSRID(ST_MakePoint(21.0067721, 52.2360178), 4326));

ALTER TABLE locations_test3 ADD CONSTRAINT pkey_locations_test3 PRIMARY KEY(id);