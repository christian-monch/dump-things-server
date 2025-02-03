
### Dump Things Service

This is an implementation of a service that stores data as described in
[Dump Things Service](https://concepts.datalad.org/dump-things).

It provides a HTTP-base API that receives the data objects.
Data objects must conform to a given schema. The service supports an arbitrary number of schemas. Objects must be JSON-encoded.

### Running the service

The basic service configuration is done via command line parameters.
The following parameters are supported:

- `<storage root>` (mandatory): the path of a directory in which the record stores are kept. It must contain two subdirectories: `global_store` and `token_stores`.
 `global_store` should be the root of a dump-thing-service store, as described in [Dump Things Service](https://concepts.datalad.org/dump-things).
 `token_stores` should contain zero or more subdirectories.
 The names of these subdirectories act as token values.
 If a respective token value is used, data will be stored in the token store.
 Configuration values, for example mapping function settings, are read from the global store.
The following shows an example for a store that is at location `data-storage/store`, has two record collections, `schema_1` and `schema_2`, and a single token store, named `token_1` (both record collections contains the same object of type `Person`, but they have a different file-system layout because they use different mapping functions):

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
```

- `--host` (optional): the IP address of the host the service should run on


- `--port`: the port number the service should listen on

The service can be started via `hatch` like this:

```bash
hatch run fastapi:run /data-storage/store
```
In this example the service will run on the network location `0.0.0.0:8000` and provide access to the stores under `/data-storage/store`.

To run the service on a specific host and port, use the command line options `--host` and `--port`, for example:

```bash
hatch run fastapi:run /data-storage/store --host 127.0.0.1 --port 8000
```

### Endpoints

Most endpoints require an *interoperability-label*. These correspond to the names of the "data record collection"-directories (for example `myschema-v3-fmta` in [Dump Things Service](https://concepts.datalad.org/dump-things/)) in the stores.

The service provides the following endpoints:

- `POST /<interoperability-label>/record/<class>`: an object of type `<class>` (defined by the schema associated with `<interoperability-label>`) can be posted to this endpoint.
 The object-content must be JSON-encoded.
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
