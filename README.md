
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

The service is configured by specifying the root of a data store.
This id done via the environment variable `DUMP_THINGS_STORAGE_PATH`.


#### Running the service

Once a configuration file is created, the service can be run with the following command:

```bash
hatch run fastapi:dev
```

#### Restrictions

The current implementation has the following restrictions:

- does not yet support any other data format than `yaml`
- does not yet support extraction of inlined records
