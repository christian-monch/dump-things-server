
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
 Configuration values, for example, mapping function settings, are read from the global store.
The following shows an example for a store that is at location `data-storage/store`, has two record collections, `collection_1` and `collection_2`, and a single token store, named `token_1` (both record collections contains the same object of type `Person`, but they have a different file-system layout because they use different mapping functions):

```
/data-storage/store
├── global_store
│   ├── .dumpthings.yaml
│   ├── collection_1
│   │   ├── .dumpthings.yaml
│   │   └── Person
│   │       └── f2cdfa3142add5791dc6fe45209206fd.yaml
│   └── collection_2
│       ├── .dumpthings.yaml
│       └── Person
│           └── f2c
│               └── dfa3142add5791dc6fe45209206fd.yaml
└── token_stores
    └── token_1
        ├── .token_config.yaml
        ├── collection_1
        :   :
```

#### Configuring token stores

To write records to the service, a token must be provided.
This token must match a subdirectory-name in `token_stores`, in the example above `token_1` would be a valid token.
Token stores can be configured to allow or disallow reading of records and to allow or disallow writing of records.
This is done via the configuration file `.token_config.yaml` in the token store.
The token configuration supports two keys: `read_access` and `write_access`.
The values of the keys should be boolean values, i.e. `true` or `false`.
If no configuration file is present, the default values are `true` for both keys.


###### Example: configure a site to allow only token-based read and write access to token store data and global data.

With token store configurations the service can be configured in such a way that any API operation requires a recognized token, without a token no records are reported or accepted.
This includes records that are stored in the global store.
To implement this scenario, the service must be started with the `--no-global-store` flag.
The flag will ensure that the service only looks for records in the token stores.
If records from the global store should be accessible in addition via a specific token, the corresponding token store must contain links to the respective collection or classes in the global store.
The `.token_config.yaml` files of the individual token stores determine whether the tokens can be used to read or write records.

A word of caution: if the token store is configured to allow write access and contains links into the global store, a write operation would modify the global store, i.e. the curated data.



#### Command line parameters:

The service supports the following command line parameters:

- `--host` (optional): the IP address of the host the service should run on


- `--port`: the port number the service should listen on


- `--no-global-store`: if set, the service will only search for records in the token-store associated with a token. If no token is provided, no records will be found.

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

Most endpoints require a *collection*. These correspond to the names of the "data record collection"-directories (for example `myschema-v3-fmta` in [Dump Things Service](https://concepts.datalad.org/dump-things/)) in the stores.

The service provides the following endpoints:

- `POST /<collection>/record/<class>`: an object of type `<class>` (defined by the schema associated with `<collection>`) can be posted to this endpoint.
 The object-content must be JSON-encoded.
 In order to `POST` an object to the service, you MUST provide a valid token in the HTTP-header `X-DumpThings-Token`. This token has to correspond to a token value defined in the configuration file.
 In addition, the `content-type`-header must be set to `application/json`.
 The endpoint supports the query parameter `format`, to select the format of the posted data.
 It can be set to `json` (the default) or to `ttl` (Terse RDF Triple Language, a.k.a. Turtle).
 If the `ttl`-format is selected, the content-type should be `text/turtle`.  
 The service supports extraction of inlined records as described in [Dump Things Service](https://concepts.datalad.org/dump-things/).
 On success the endpoint will return a list of all stored records.
 This might be more than one record if the posted object contains inlined records.
  
- `GET /<collection>/records/<class>`: retrieve all objects of type `<class>` or any of its subclasses that are stored in a token storage space or the global storage space of the service.
 If the service was started with the `--no-global-store` flag, records in the global storage space will be ignored. 
 If a token is provided, all matching objects from the token storage space are returned.
  If the service was started with the `--no-global-store` flag, it will only return objects from the token storage space, otherwise the service returns objects from the global storage space in addition.
 Objects from token space take precedence over objects from the global space, i.e. if there are two objects with identical `pid` in the global store and the object store, the record from the token store will be returned.
 The endpoint supports the query parameter `format`, which determines the format of the query result.
 It can be set to `json` (the default) or to `ttl`,


- `GET /<collection>/record?pid=<pid>`: retrieve an object with the pid `<pid>` from a token storage space or from the global storage of the service.
  If the service was started with the `--no-global-store` flag, records in the global storage space will be  ignored.
  If a token is provided, the object is first searched in the token storage space.
  If the service was started with the `--no-global-store` flag, it will only search in the token storage space, otherwise the service will also search in the global storage space in addition.
  Only objects with a type defined by the schema associated with `<collection>` are considered.
  The endpoint supports the query parameter `format`, which determines the format of the query result.
  It can be set to `json` (the default) or to `ttl`,


- `GET /docs`: provides information about the API of the service, i.e. about all endpoints.


#### Restrictions

The current implementation has the following restriction:

- does not yet support any other data format than `yaml`


### Acknowledgements

This work was funded, in part, by

- Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under grant TRR 379 (546006540, Q02 project)


- MKW-NRW: Ministerium für Kultur und Wissenschaft des Landes Nordrhein-Westfalen under the Kooperationsplattformen 2022 program, grant number: KP22-106A
