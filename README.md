
### Dump Things Service

This is an implementation of a service that allows to store and retrieve data that is structured according to given schemata.

Data is stored in **collections**.
Each collection has a name and an associated schema.
All data records in the collection have to adhere to the given schema.

The general workflow in the service is as follows.
We distinguish between two areas of a collection, an **incoming** are and a **curated** area.
Data written to a collection is stored in a collection-specific **incoming** area.
A curation process, which is outside the scope of the service, moves data from the incoming area of a collection to the **curated** area of the collection.

In order to submit a record to a collection, a token is required.
The token defines read- and write- permissions for the incoming areas of collections and read-permissions for the curated area of a collection.
A token can carry permissions for multiple collections.
In addition the token carries a submitter ID.
It also defines a token specific **zone** in the incoming area.
So any read- and write-operations on an incoming area are actually restricted to the token-specific zone in the incoming area.
Multiple tokens can share the same zone.
That allows multiple submitters to work together when storing records in the service.

The service provides a HTTP-based API to store and retrieve data objects, and to verify token capabilities.


### Running the service

The basic service configuration is done via command line parameters and configuration files.

The following command line parameters are supported:

- `<storage root>`: (mandatory) the path of a directory that serves as anchor for all relative paths given in the configuration files. Unless `-c/--config` is provided, the service will search the configuration file in `<storage root>/.dumpthings.yaml`.

- `--host <IP-address>`: The IP-address on which the service should accept connections (default: `0.0.0.0`).

- `--port <port>`: The port on which the service should accept connections (default: `8000`).

- `-c/--config <config-file>`: provide a path to the configuration file. The configuration file in `<storage root>/.dumpthings.yaml` will be ignored, if it exists at all.

- `--origins <origin>`: add a CORS origin hosts (repeat to add multiple CORS origin URLs).`

- `--root-path <path>`: Set the ASGI 'root_path' for applications submounted below a given URL path.


### Configuration file

The service is configured via a configuration file that defines collections, pathes for incoming and curated data for each collection, as well as token properties.
Token properties include a submitter identification and for each collection an incoming zone specifier, permissions for reading and writing of the incoming zone and permission for reading the curated data of the collection.

A "formal" definition of the configuration file is provided by the class `GlobalConfig` in the file `dumpthings-server/config.py`.

Configurations are read in YAML format. The following is an example configuration file that illustrates all options:

```yaml
type: collections     # has to be "collections"
version: 1            # has to be 1

# All collections are listed in "collections"
collections:

  # The following entry defines the collection "personal_records"
  personal_records:
    # The token, as defined below, that is used if no token is provided by a client.
    # All tokens that are provided by the client will be OR-ed with the default token.
    # That means all permissions in the default token will be added to the client provided
    # token. In this way the default token will always be less or equally powerful as the
    # client provided token.
    default_token: no_access

    # The path to the curated data of the collection. This path should contain the
    # ".dumpthings.yaml"-configuration for  collections that is described
    # here: <https://concepts.datalad.org/dump-things/>.
    # A relative path is interpreted relative to the storage root, which is provided on
    # service start. An absolute path is interpreted as an absolute path.
    curated: curated/personal_records

    # The path to the incoming data of the collection.
    # Different collections should have different curated- and incoming-paths
    incoming: /tmp/personal_records/incoming

  # The following entry defines the collection "rooms_and_buildings"
  rooms_and_buildings:
    default_token: basic_access
    curated: curated/rooms_and_buildings
    incoming: incoming/rooms_and_buildings

  # The following entry defines the collection "fixed_data", which does not
  # support data uploading, because there is no token that allows uploads to 
  # "fixed_data".
  fixed_data:
    default_token: basic_access
    # If not upload is supported, the "incoming"-entry is not necessary.
    curated: curated/fixed_data_curated

# All tokens are listed in "tokens"
tokens:
  
  # The following entry defines the token "basic_access". This token allows read-only
  # access to the two collections: "rooms_and_buildings" and "fixed_data".
  basic_access:

    # The value of "user-id" will be added as an annotation to each record that is
    # uploaded with this token.
    user_id: anonymous

    # The collections for which the token holds rights are defined in "collections"
    collections:

      # The rights that "basic_access" carries for the collection "rooms_and_buildings"
      # are defined here.
      rooms_and_buildings:
        # Access modes are defined here:
        # <https://github.com/christian-monch/dump-things-server/issues/67#issuecomment-2834900042>
        mode: READ_CURATED

        # A token and collection-specific label, that defines "zones" in which incoming
        # records are stored. Multiple tokens can share the same zone, for example if
        # many clients with individual tokens work together to build a collection.
        # (Since this token does not allow right access, "incoming_label" is ignored and
        # left empty here (TODO: it should not be required in this case)).
        incoming_label: ''

      # The rights that "basic_access" carries for the collection "fixed_data"
      # are defined here.
      fixed_data:
        mode: READ_CURATED
        incoming_label: ''

  # The following entry defines the token "no_access". This token does not allow
  # any access and is used as a default token for the collection "personal_records".
  no_access:
    user_id: nobody

    collections:
      personal_records:
        mode: NOTHING
        incoming_label: ''

  # The following entry defines the token "admin". It gives full access rights to
  # the collection "personal_records".
  admin:
    user_id: Admin
    collections:
      personal_records:
        mode: WRITE_COLLECTION
        incoming_label: 'admin_posted_records'

  # The following entry defines the token "contributor_bob". It gives full access
  # to "rooms_and_buildings" for a user with the id "Bob".
  contributor_bob:
    user_id: Bob
    collections:
      rooms_and_buildings:
        mode: WRITE_COLLECTION
        incoming_label: new_rooms_and_buildings
        
  # The following entry defines the token "contributor_alice". It gives full access
  # to "rooms_and_buildings" for a user with the id "Alice". Bob and Alice share the
  # same incoming-zone, i.e. "new_rooms_and_buildings". That means they can read
  # incoming records that the other one posted.
  contributor_alice:
    user_id: Alice
    collections:
      rooms_and_buildings:
      mode: WRITE_COLLECTION
      incoming_label: new_rooms_and_buildings
```

#### Command line parameters:

The service supports the following command line parameters:

- `<storage root>`: this is a mandatory parameter that defines the directory that serves as root for relative `curated`- and `incoming`-paths. Unless the `-c/--config` option is given, the configuration is loaded from `<storage root>/.dumpthings.yaml`.

- `--host`: (optional): the IP address of the host the service should run on


- `--port`: the port number the service should listen on


- `-c/--config`: if set, the service will read the configuration from the given path. Otherwise it will try to read the configuration from `<storage root>/.dumpthings.yaml`.

- `--error-mode`: if set, the service will run even if an error prevents it from starting properly. It will report the error on every request. This can be useful if the service is deployed automatically and a no other monitoring method is available.

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


- `POST /<collection>/token_permissions`: post an object of type `TokenCapabilityRequest` (JSON-encoded) to receive the permission flags and the zone-label of the specified token, or of the default token. 


- `GET /docs`: provides information about the API of the service, i.e. about all endpoints.


#### Restrictions

The current implementation has the following restriction:

- does not yet support any other data format than `yaml`


### Acknowledgements

This work was funded, in part, by

- Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under grant TRR 379 (546006540, Q02 project)


- MKW-NRW: Ministerium für Kultur und Wissenschaft des Landes Nordrhein-Westfalen under the Kooperationsplattformen 2022 program, grant number: KP22-106A
