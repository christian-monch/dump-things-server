
### Dump Things Service

This is an implementation of a service that stores data as described in
[Dump Things Service](https://concepts.datalad.org/dump-things-service) that uses the [DataLad Concepts Toolkit](https://concepts.datalad.org/dump-things).

It provides a HTTP-base API that receives the data objects.
Data objects must conform to a given schema. The service supports an arbitrary number of schemas.

##### URLs for endpoints

The URL-path for a data object of class `<Class>` of schema `<Schema>` with the schema version `<Version>` is `/dump/<Schema>/<Version>/<Class>`.
If the server runs for example on network address `http://localhost:8080`, the URL would be `http://localhost:8080/dump/<Schema>/<Version>/<Class>`.

The endpoints support POST-requests, data object have to be URL-encoded. For example, and object with JSON-representation `{"name": "Alice", "age": 43}` would be encoded as `name=Alice&age=43`.

#### Configuration

The service is configured by a YAML-file. If no file is provided, `./dumpthings-conf.yaml` is used. An alternative configuration file path can be specified vie the environment variable `DUMPTHINGS_CONF`.

The configuration currently supports the following keys:

* `schemas`: a list of schema-ids, i.e. IRIs
* `storage_path`: a path where objects should be stored (if no store exists, it will be created)

Both keys are mandatory.
An example for a valid configuration file is:

    schema_ids:
        - "https://concepts.trr379.de/s/base/unreleased.yaml"

    storage_path: /tmp/root5


#### Running the service

Once a configuration file is created, the service can be run with the following command:

```bash
hatch run fastapi:dev
