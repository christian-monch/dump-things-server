
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
In addition, the token carries a submitter ID.
It also defines a token specific **zone** in the incoming area.
So any read- and write-operations on an incoming area are actually restricted to the token-specific zone in the incoming area.
Multiple tokens can share the same zone.
That allows multiple submitters to work together when storing records in the service.

The service provides a HTTP-based API to store and retrieve data objects, and to verify token capabilities.

### Installing the service

The service is available via `pypi`, and can be installed by `pip`.
Execute the command `pip install dump-things-service` to install the service.


### Running the service

After installation the service can be started via the command `dump-things-service`. 
The basic service configuration is done via command line parameters and configuration files.

The following command line parameters are supported:

- `<storage root>`: (mandatory) the path of a directory that serves as anchor for all relative paths given in the configuration files. Unless `-c/--config` is provided, the service will search the configuration file in `<storage root>/.dumpthings.yaml`.

- `--host <IP-address>`: The IP-address on which the service should accept connections (default: `0.0.0.0`).

- `--port <port>`: The port on which the service should accept connections (default: `8000`).

- `-c/--config <config-file>`: provide a path to the configuration file. The configuration file in `<storage root>/.dumpthings.yaml` will be ignored, if it exists at all.

- `--origins <origin>`: add a CORS origin hosts (repeat to add multiple CORS origin URLs).`

- `--root-path <path>`: Set the ASGI 'root_path' for applications submounted below a given URL path.

- `--sort-by <field>`: By default result records are sorted by the field `pid`.
  This parameter allows overriding the sort field.
  The parameter can be repeated to define secondary, tertiary, etc. sorting fields.
  If a given field is not present in the record, the record will be sorted behind all records that possess the field.

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

#### Backends

The service currently supports the following backends for storing records:
- `record_dir`: this backend stores records as YAML-files in a directory structure that is defined [here](https://concepts.datalad.org/dump-things/). It reads the backend configuration from a "record collection configuration file" as described [here](https://concepts.datalad.org/dump-things/).

- `sqlite`: this backend stores records in a SQLite database. There is an individual database file, named `records.db`, for each curated area and incoming area.

Backends can be defined per collection in the configuration file.
If no backend is defined for a collection, the `record_dir`-backend is used by default.
The following configuration snippet shows how to define a backend for a collection:

```yaml
...
collections:
  collection_with_default_record_dir_backend:
    default_token: anon_read
    curated: collection_1/curated

  collection_with_explicit_record_dir_backend:
    default_token: anon_read
    curated: collection_1/curated
    backend:
      # The record_dir-backend is identified by the
      # type: "record_dir". No more attributes are
      # defined for this backend.
      type: record_dir

  collection_with_sqlite_backend:
    default_token: anon_read
    curated: collection_2/curated
    backend:
      # The sqlite-backend is identified by the
      # type: "sqlite". It requires a schema attribute
      # that holds the URL of the schema that should
      # be used in this backend.
      type: sqlite
      schema: https://concepts.inm7.de/s/flat-data/unreleased.yaml
```

### Command line parameters:

The service supports the following command line parameters:

- `<storage root>`: this is a mandatory parameter that defines the directory that serves as root for relative `curated`- and `incoming`-paths. Unless the `-c/--config` option is given, the configuration is loaded from `<storage root>/.dumpthings.yaml`.

- `--host`: (optional): the IP address of the host the service should run on


- `--port`: the port number the service should listen on


- `-c/--config`: if set, the service will read the configuration from the given path. Otherwise it will try to read the configuration from `<storage root>/.dumpthings.yaml`.


- `--log-level`: set the log level for the service, allowed values are `ERROR`, `WARNING`, `INFO`, `DEBUG`. The default-level is `WARNING`.


- `--sort-by`: sort results by the given fields. Multiple fields can be specified, e.g. `--sort-by pid --sort-by date` to define primary, secondary, etc. sorting fields. If a given field is not present in the record, the record will be sorted behind all records that possess the field.


- `--export-to`: export all data in `<storage root>` as JSON to the given path and exit. If the path is `-`, the data will be written to `stdout`. The data in `<storage root>` will not be modified. This is useful to export the data for backup or migration purposes. The file will contain all records in all collections. NOTE: the resulting file might be large.


- `--export-json`: an alias for `export-to`.


- `--export-tree`: export all data in `<storage root>` as file tree at the given path. The tree confirms to the [dumpthings-specification](https://concepts.datalad.org/dump-things/).


- `--error-mode`: if set, the service will run even if an error prevents it from starting properly. It will report that it executes in error mode on every request. This can be useful if the service is deployed automatically and no other monitoring method is available.


- `--root-path`: set the ASGI `root_path` for applications sub-mounted below a given URL path.


The service can be started with the following command:

```bash
dump-things-service
```
In this example the service will run on the network location `0.0.0.0:8000` and provide access to the stores under `/data-storage/store`.

To run the service on a specific host and port, use the command line options `--host` and `--port`, for example:

```bash
dump-things-service /data-storage/store --host 127.0.0.1 --port 8000
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
  

- `GET /<collection>/records/<class>`: retrieve all readable objects from collection `<collection>` that are of type `<class>` or any of its subclasses.that are readable .
 Objects are readable, if the default token for the collection allows reading of objects or if a token is provided that allows reading of objects in the collection.
 Objects from incoming spaces will take precedence over objects from curated spaces, i.e. if there are two objects with identical `pid` in the curated space and in the incoming space, the object from the incoming space will be returned.
 The endpoint supports the query parameter `format`, which determines the format of the query result.
 It can be set to `json` (the default) or to `ttl`,


- `GET /<collection>/records/p/<class>`: this endpoint (ending on `.../p/<class>`) provides the same functionality as the endpoint `GET /<collection>/records/<class>` (without `.../p/...`) but supports result pagination. In addition to the query parameter `format`, it supports the query parameters `page` and `size`.
 The `page`-parameter defines the page number to retrieve, starting with 1.
 The `size`-parameter defines how many records should be returned per page.
 If no `size`-parameter is given, the default value of 50 is used.
 Each response will also contain the total number of records and the total number of pages in the result.
 The response is a JSON object with the following structure:
 ```json
{
  "items": [ <JSON-record or ttl-string> ],
  "total": <total number of records in the result>,
  "page": <current page number>,
  "size": <number of records per page>,
  "pages": <number of pages in the result>
}
 ```
  In contrast to the `GET /<collection>/records/<class>` endpoint, this endpoint will return individual ttl-records, not a combination of all ttl-records in the result.


- `GET /<collection>/record?pid=<pid>`: retrieve an object with the pid `<pid>` from the collection `<collection>`, if the provided token allows reading. If the provided token allows reading of incoming and curated spaces, objects from incoming spaces will take precedence.
  The endpoint supports the query parameter `format`, which determines the format of the query result.
  It can be set to `json` (the default) or to `ttl`,


- `POST /<collection>/token_permissions`: post an object of type `TokenCapabilityRequest` (JSON-encoded) to receive the permission flags and the zone-label of the specified token, or of the default token. 


- `GET /docs`: provides information about the API of the service, i.e. about all endpoints.


### Tips & Tricks

The service can be configured in such a way that incoming records are immediately available in the curated area.
To achieve this, the final path of the incoming zone must be the same as the curated area, for example:

```yaml
type: collections
version: 1

collections:
  datamgt:
    default_token: anon_read
    curated: datamgt/curated
    incoming: datamgt

tokens:
  anon_read:
    user_id: anonymous
    collections:
      datamgt:
        mode: READ_CURATED
        incoming_label: ""

  trusted-submitter-token:
    user_id: trusted_submitter
    collections:
      datamgt:
        mode: WRITE_COLLECTION
        incoming_label: "curated"
```
In this example the curated area is `datamgt/curated` and the incoming area for the token `trusted-submitter-token` is `datamgt` plus the incoming zone `curated`, i.e., `datamgt/curated` which is exactly the curated area defined for `collection_1`.


### Restrictions

The current implementation has the following restriction:

- the `record_dir`-backend does not yet support any other data format than `yaml`.


## Acknowledgements

This work was funded, in part, by

- Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under grant TRR 379 (546006540, Q02 project)


- MKW-NRW: Ministerium für Kultur und Wissenschaft des Landes Nordrhein-Westfalen under the Kooperationsplattformen 2022 program, grant number: KP22-106A
