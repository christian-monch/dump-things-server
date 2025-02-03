
### Dump Things Service

This is an implementation of a service that stores data as described in
[Dump Things Service](https://concepts.datalad.org/dump-things).

It provides a HTTP-base API that receives the data objects.
Data objects must conform to a given schema. The service supports an arbitrary number of schemas.

### Running the service

The basic service configuration is done via command line parameters.
The following parameters are supported:

- `<storage root>` (mandatory): the path of a directory in which the record stores are kept. It must contain two subdirectories: `global_store` and `token_stores`.
 `global_store` should be the root of a dump-thing-service store, as described in [Dump Things Service](https://concepts.datalad.org/dump-things).
 `token_stores` should contain zero or more subdirectories.
 The names of these subdirectories act as token values.
 Each of these subdirectories should contain a dumpt-things-service store with the same configuration as `global_store`, i.e. it should have the same `.dumpthings.yaml` files.
The following shows an example for stores that are location as `data-storage/store`:

```
/data-storage/store
├── global_store
│   ├── .dumpthings.yaml
│   ├── schema_1
│   │   ├── .dumpthings.yaml
│   │   └── Person
│   │       └── f2cdfa3142add5791dc6fe45209206fd.yaml
│   ├── schema_2
│   │   ├── .dumpthings.yaml
│   │   └── Person
│   │       └── f2c
│   │           └── dfa3142add5791dc6fe45209206fd.yaml
└── token_stores
    └── token_1
        ├── .dumpthings.yaml
        ├── schema_1
        │   ├── .dumpthings.yaml
        │   └── Person
        │       └── f2cdfa3142add5791dc6fe45209206fd.yaml
        └── schema_2
            ├── .dumpthings.yaml
            └── Person
                └── f2c
                    └── dfa3142add5791dc6fe45209206fd.yaml
```

- `--host` (optional): the IP address of the host the service should run on


- `--port`: the port number the service should listen on

The service can be started via `hatch` like this:

```bash
hatch run fastapi:run /data-storage/store --host 127.0.0.1 --port 8000
```

In this example the service will run on the network location `127.0.0.1:8000` and provide access to the stores under `/data-storage/store`.

### Endpoints

Most endpoints require an *interoperability-label*. These correspond to the names of the "data record collection"-directories (see [Dump Things Service](https://concepts.datalad.org/dump-things/)) in the stores.

The service provides the following endpoints:

- `POST /<interoperability-label>/record/<class>`: an object of type `<class>` (defined by the schema associated with `<interoperability-label>`) can be posted to this endpoint.
 The object-content must be form-encoded.
 In order to `POST` an object to the service, you MUST provide a valid token in the HTTP-header `X-DumpThings-Token`. This token has to correspond to a token value defined in the configuration file.


- `GET /<interoperability-label>/records/<class>`: retrieve all objects of type `<class>` (defined by the schema associated with `<interoperability-label>`) that are stored in the global storage space of the service.
 If a token is provided, all matching objects from the token storage space are returned in addition.


- `GET /<interoperability-label>/record/<id>`: retrieve an object with the id `<id>` from the global storage of the service. If a token is provided, the object is also searched in the token storage space. Only objects with a type defined by the schema associated with `<interoperability-label>` are considered.


- `GET /docs`: provides information about the API of the service, i.e. about all endpoints.


#### Restrictions

The current implementation has the following restrictions:

- does not yet support any other data format than `yaml`
- does not yet support extraction of inlined records
- does not yet find subclasses of a searched class
- token storage should have the same configuration as the global storage, this is currently not enforced or verified
