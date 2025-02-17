
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
│   └── schema_2
│       ├── .dumpthings.yaml
│       └── Person
│           └── f2c
│               └── dfa3142add5791dc6fe45209206fd.yaml
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

Most endpoints require an *collection*. These correspond to the names of the "data record collection"-directories (for example `myschema-v3-fmta` in [Dump Things Service](https://concepts.datalad.org/dump-things/)) in the stores.

The service provides the following endpoints:

- `POST /<collection>/record/<class>`: an object of type `<class>` (defined by the schema associated with `<collection>`) can be posted to this endpoint.
 The object-content must be JSON-encoded.
 In order to `POST` an object to the service, you MUST provide a valid token in the HTTP-header `X-DumpThings-Token`. This token has to correspond to a token value defined in the configuration file.
 In addition, the `content-type`-header must be set to `application/json`.
 The endpoints supports the query parameter `format`, to select the format of the posted data.
 It can be set to `json` (the default) or to `ttl`.
 If the `ttl`-format is selected, the content-type should be `text/turtle`.  
 The service supports extraction of inlined records as described in [Dump Things Service](https://concepts.datalad.org/dump-things/).
  
- `GET /<collection>/records/<class>`: retrieve all objects of type `<class>` or any of its subclasses that are stored in the global storage space of the service.
 If a token is provided, all matching objects from the token storage space are returned in addition.
 Objects from token space take precedence over objects from the global space.
 The endpoints supports the query parameter `format`, which determines the format of the query result.
 It can be set to `json` (the default) or to `ttl`,


- `GET /<collection>/record?id=<id>`: retrieve an object with the id `<id>` from the global storage of the service. If a token is provided, the object is also searched in the token storage space. Only objects with a type defined by the schema associated with `<collection>` are considered.
  The endpoints supports the query parameter `format`, which determines the format of the query result.
  It can be set to `json` (the default) or to `ttl`,


- `GET /docs`: provides information about the API of the service, i.e. about all endpoints.


#### Restrictions

The current implementation has the following restriction:

- does not yet support any other data format than `yaml`


### Acknowledgements

This work was funded, in part, by

- Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under grant TRR 379 (546006540, Q02 project)


- MKW-NRW: Ministerium für Kultur und Wissenschaft des Landes Nordrhein-Westfalen under the Kooperationsplattformen 2022 program, grant number: KP22-106A
