## PostGIS database

Building docker image:
```docker build -t tbochens/spdbgis .```

Running docker container:
```docker run --name spdb-database -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 tbochens/spdbgis```

Ensuring that container initialization is done:
```docker logs <container_id>```

If logs contain *Maps data loaded* log, database is ready for using.

Connecting to database from local machine:
```psql -h localhost -p 5432 -U postgres```
