
### Dump Things Service

This is an implementation of a service that stores data as described in
[Dump Things Service](https://concepts.datalad.org/dump-things-service) that uses the [DataLad Concepts Toolkit](https://concepts.datalad.org/dump-things).

It provides a HTTP-base API that receives the data objects.
Data objects must conform to a given schema. The service supports an arbitrary number of schemas.

### Running the service

The basic service configuration is done via a YAML-file that contains the following top level keys:

- `host`: the value is the IP address of the host the service should run on


- `port`: the value is the port the service should listen on


- `global_store`: the value is the path of the record store for token-less access


- `token_stores`: a dictionary with token values as keys and the corresponding record store paths as values

The stores themselves have to be structured as described in the [Dump Things Service](https://concepts.datalad.org/dump-things/) documentation.

A configuration file could look like this:

```yaml
host: 127.0.0.1
port: 8000
global_store: /data-storage/store
token_stores:
  token1: /data-storage/token1_store
  token2: /data-storage/token2_store
```

Once a configuration file is created, the service has to be informed about the location of the config file.
This is done via the environment variable `DUMPTHINGS_CONFIG_FILE`, which should contain the path of the config file that should be used.
If this environment variable is not set, the service will look for the file `./dumpthings_conf.yaml`.
If no such file is found, the service will not start successfully.

The service can be started with the following command:

```bash
hatch run fastapi:run <path-to-config-file> 
```


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
