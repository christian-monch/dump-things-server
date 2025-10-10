### Dump Things Service

[![PyPI version fury.io](https://badge.fury.io/py/dump-things-service.svg)](https://pypi.python.org/pypi/dump-things-service/)

This is an implementation of a service that allows to store and retrieve data that is structured according to given schemata.

Data is stored in **collections**.
Each collection has a name and an associated schema.
All data records in the collection have to adhere to the given schema.

The canonical format for schemas is [LinkML](https://linkml.io/).
The service supports schemas that are based on Datalad's *Thing* schema, i.e. on [https://concepts.datalad.org/s/things/v1/](https://concepts.datalad.org/s/things/v1/).
It assumes that the classes of stored records are subclasses of `Thing`, and inherit the properties `pid` and `schema_type` from the `Thing`-baseclass.

The general workflow in the service is as follows.
We distinguish between two areas of a collection, an **incoming** are and a **curated** area.
Data written to a collection is stored in a collection-specific **incoming** area.
A curation process, which is outside the scope of the service, moves data from the incoming area of a collection to the **curated** area of the collection.

To submit a record to a collection, a token is required.
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

The service is configured via a configuration file that defines collections, paths for incoming and curated data for each collection, as well as token properties.
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
        # (Since this token does not allow write access, "incoming_label" is ignored and
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

  # The following entry defines a hashed token because the key `hashed` is set
  # to `True`. A hashed token has the structure
  # `<id>-<sha256>`. It will match an incoming token if the incoming token has
  # the structure `<id>-<content>` and if sha256(`<content>`) equals `<sha256>`.
  # In this example, if the client present sthe token `bob-hello`, he will be
  # granted access because `sha256('hello')` equals
  # `2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824`
  bob-2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824:
    hashed: True
    collections:
      rooms_and_buildings:
      mode: WRITE_COLLECTION
      incoming_label: bob
    
  #
```

#### Backends

The service currently supports the following backends for storing records:
- `record_dir`: this backend stores records as YAML-files in a directory structure that is defined [here](https://concepts.datalad.org/dump-things-storage-v0/). It reads the backend configuration from a "record collection configuration file" as described [here](https://concepts.datalad.org/dump-things-storage-v0/).

- `sqlite`: this backend stores records in a SQLite database. There is an individual database file, named `__sqlite-records.db`, for each curated area and incoming area.

- `record_dir+stl`: here `stl` stands for "schema-type-layer".
  This backend stores records in the same format as `record_dir`, but adds special treatment for the `schema_type` attribute in records.
  It removes `schema_type`-attributes from the top-level mapping of a record before storing it as YAML-file. When records are read from this backend, a `schema_type` attribute is added back into the record, using a schema to determine the correct class-URI.
  In other words, all records stored with this backend will have no `schema_type`-attribute in the top-level, and all records read with this backend will have a `schema_type` attribute in the top-level.

- `sqlite+stl`: This backend stores records in the same format as `sqlite`, but adds the same special treatment for the `schema_type` attribute as `record_dir+stl`.

Backends can be defined per collection in the configuration file.
The backend will be used for the curated area and for the incoming areas of the collection.
If no backend is defined for a collection, the `record_dir+stl`-backend is used by default.
The `+stl`-backends can be useful if an endpoint returns records of multiple classes, because it allows clients to determine the class of each result record.

The service guarantees that backends of all types can co-exist independently in the same directory, i.e., there are no name collisions in files that are used for different backends (as long as no class name starts with `.` or `_`)).

The following configuration snippet shows how to define a backend for a collection:

```yaml
...
collections:
  collection_with_default_record_dir+stl_backend:
    # This is a collection with the default backend, i.e. `record_dir+stl` and
    # the default authentication, i.e. config-based authentication.
    default_token: anon_read
    curated: collection_1/curated

  collection_with_forgejo_authentication_source:
    # This is a collection with the default backend, i.e. `record_dir+stl` and
    # a forgejo-based authentication source. That means it will use a forgejo
    # instance to determine the permissions of a token for this collection.
    # The instance is also used to determine the user-id and the incoming label.
    # In the case of forgejo, the user-id and the incoming label are the
    # forgejo login associated with the token.

    # We still need the name of a default token. If the token is defined in this
    # config file, its properties will be determined by the
    # config file. If the token is not defined in the config file, its
    # properties will be determined by the authentication sources. In this
    # example by the forgejo-instance at `https://forgejo.example.com`.
    # If there is more than one authentication source, they will be tried
    # in the order they are defined in the config file.
    default_token: anon_read    # We still need a default token
    curated: collection_2/curated

    # Token permissions, user-ids (for record annotations), and incoming
    # label can be determined by multiple authentication sources.
    # If no source is defined, `config` will be used, which reads token
    # information from the config file.
    # This example explicitly defines `config` and a second authentication
    # source, a `forgejo` authentication source.
    auth_sources:
      - type: forgejo   # requires `user`-read and `organization`-read permissions on token
        # The API-URL of the forgejo instance that should be used
        url: https://forgejo.example.com/api/v1
        # An organization
        organization: data_handling
        # A team in the organization. The authorization of the team
        # determines the permissions of the token
        team: data_entry_personal
        # `label_type` determines how an incoming label is created for
        # a Forgejo token. If `label_type` is `team`, the incoming label
        # will be `forgejo-team-<organization>-<team>`. If `label_type`
        # is `user`, the incoming label will be 
        # `forgejo-user-<user-login>`
        label_type: team
        # An optional repository. The token will only be authorized
        # if the team has access to the repository. Note: if `repo`
        # is set, the token must have at least repository read
        # permissions.
        repo: reference-repository

      # Fallback to the config file.
      - type: config    # check tokens from the configuration file

      # Multiple authorization sources are allowed. They will be tried in the
      # order defined in the config file. If an authorization source returns
      # permissions for a token, those permissions will be used and no other
      # authorization sources will be queried.
      # The default authorization source is `config`, which reads the token 
      # permissions, user-id, and incoming
  
  collection_with_explicit_record_dir+stl_backend:
    default_token: anon_read
    curated: collection_3/curated
    backend:
      # The record_dir-backend is identified by the
      # type: "record_dir". No more attributes are
      # defined for this backend.
      type: record_dir+stl

  collection_with_sqlite_backend:
    default_token: anon_read
    curated: collection_4/curated
    backend:
      # The sqlite-backend is identified by the
      # type: "sqlite". It requires a schema attribute
      # that holds the URL of the schema that should
      # be used in this backend.
      type: sqlite
      schema: https://concepts.inm7.de/s/flat-data/unreleased.yaml
```

#### Authentication and authorization

To authenticate and authorize a user based on tokens, dumpthing-service uses
authentication sources. There are currently two authentication sources: the
configuration file and a Forgejo-based authentication source. Authentication
sources can be configured per collection. If no authentication source is
configured, the collection uses the configuration file. 

If authentication sources are configured, they will be tried in order until
a token is authenticated. If an authentication source is listed twice, the
second instance will be ignored.

Authentication sources can be defined individually for each collection.
The collection-level key `auth_sources` should contain a list of authentication source configurations.
Authentication sources are tried in order until a token is successfully authenticated.
If no authentication source authenticates the token, the token will be rejected.

If no authentication source is defined, the configuration file will be used to authenticate tokens.
If an authentication source is defined multiple times, the first instance will be queried, all other instances will be ignored.

These authentication sources are available:

- config: use the configuration file to 
- forgejo: use a Forgejo-instance to authenticate tokens

All authentication source configurations contain the key `type`.
Additional keys are authentication source type-specific.

The following configuration snippet contains an example for authentication
source configuration:

```yaml
collections:
  collection_with_config_and_forgejo_auth_sources:
      # Token permissions, user-ids (for record annotations), and incoming
      # label can be determined by multiple authentication sources.
      # If no source is defined, `config` will be used, which reads token
      # information from the config file.
      # This example explicitly defines `config` and a second authentication
      # source, a `forgejo` authentication source.
      auth_sources:
        - type: forgejo   # requires `user`-read and `organization`-read permissions on token
          # The API-URL of the forgejo instance that should be used
          url: https://forgejo.example.com/api/v1
          # An organization
          organization: data_handling
          # A team in the organization. The authorization of the team
          # determines the permissions of the token
          team: data_entry_personal
          # `label_type` determines how an incoming label is created for
          # a Forgejo token. If `label_type` is `team`, the incoming label
          # will be `forgejo-team-<organization>-<team>`. If `label_type`
          # is `user`, the incoming label will be 
          # `forgejo-user-<user-login>`
          label_type: team
          # An optional repository. The token will only be authorized
          # if the team has access to the repository. Note: if `repo`
          # is set, the token must have at least repository read
          # permissions.
          repo: reference-repository
    
        # Fallback to the config file.
        - type: config    # check tokens from the configuration file
    
        # Multiple authorization sources are allowed. They will be tried in the
        # order defined in `auth_sources`. If an authorization source returns
        # permissions for a token, those permissions will be used and no other
        # authorization sources will be queried.
        # The default authorization source is `config`, which reads the token 
        # permissions, user-id, and incoming

...

```


##### Config-based authentication

```yaml
collections:
  collection_with_config_authentication:
    default_token: anon_read
    curated: collection_5/curated
    auth_sources:
      - type: <must be 'config'>    # check tokens from the configuration file

...
```
The configuration file will be used to authenticate tokens


##### Forgejo-based authentication

```yaml
collections:
  collection_with_forgejo_authentication:
    default_token: anon_read
    curated: collection_5/curated
    auth_sources:
      - type: <must be 'forgejo'>
        url: <Forgejo API-URL>
        organization: <organization name>
        team: <team_name>
        label_type: <'team' or 'user'>
        repository: <repository name>  # Optional
...
```

The defined Forgejo-instance will be used to authenticate a token

The user ID is the email of the user.

If `label_type` is set to `team`, the incoming label is `forgejo-team-<organization-name>-<team-name>`.
If `label_type` is set to `user`, the incoming label is `forgejo-user-<user-login>`

The permissions will be fetched from the unit `repo.code` of the team definition.
The following mapping is used

| `repo.code` | curated_read | incoming_read | incoming_write |
| ------------- | ------------- | ------------- | ------------- |
| `none` | `False` | `False` | `False` |
| `read` | `True` | `True` | `False` |
| `write` | `True` | `True` | `True` |


A Forgejo authentication source can authenticate Forgejo-tokens that have at least the following `Read`-permissions:

- User: this is required to determine user-related information, i.e. user-email and user login name.
- Organization: this is required to determine the membership of a user to a team in an organization.
- Repository (only if `repository` is set in the configuration): required to determine a team's access to the repository.


#### Submission annotation tag

The service annotates submitted records with a submitter id and a timestamp.
Annotations consist of an annotation tag, defining the class of the annotation, and an annotation value.
By default the service will use the class `http://purl.obolibrary.org/obo/NCIT_C54269` for the submitter id and the class `http://semanticscience.org/resource/SIO_001083` for submission time.
(Both tags will be converted into CURIEs if the schema of the collection defines an appropriate prefix.)

The default annotation tag classes can be overridden in the configuration on a per collection basis.
To override the defaults tags, add a `submission_tags`-attribute to a collection definition.
The `submission_tags`-attribute should contain a mapping that maps either `submitter_id_tag`, or `submitter_time_tag` or both to an IRI or a CURIE.
If the schema defines a matching prefix, IRIs are automatically converted to CURIEs before storing the record.
The service validates that the prefix of a CURIE is defined in the schema of the collection.

```yaml
type: collections
version: 1
collections:
  collection_1:
    default_token: basic_access
    curated: curated
    incoming: contributions
    submission_tags:
      submitter_id_tag: schema:user_id
      submission_time_tag: schema:time

  ...

```

The service currently supports the following backends for storing records:
- `record_dir`: this backend stores records as YAML-files in a directory structure that is defined [here](https://concepts.datalad.org/dump-things-storage-v0/). It reads the backend configuration from a "record collection configuration file" as described [here](https://concepts.datalad.org/dump-things-storage-v0/).

- `sqlite`: this backend stores records in a SQLite database. There is an individual database file, named `__sqlite-records.db`, for each curated area and incoming area.

- `record_dir+stl`: here `stl` stands for "schema-type-layer".
  This backend stores records in the same format as `record_dir`, but adds special treatment for the `schema_type` attribute in records.
  It removes `schema_type`-attributes from the top-level mapping of a record before storing it as YAML-file. When records are read from this backend, a `schema_type` attribute is added back into the record, using a schema to determine the correct class-URI.
  In other words, all records stored with this backend will have no `schema_type`-attribute in the top-level, and all records read with this backend will have a `schema_type` attribute in the top-level.

- `sqlite+stl`: This backend stores records in the same format as `sqlite`, but adds the same special treatment for the `schema_type` attribute as `record_dir+stl`.

Backends can be defined per collection in the configuration file.
The backend will be used for the curated area and for the incoming areas of the collection.
If no backend is defined for a collection, the `record_dir+stl`-backend is used by default.
The `+stl`-backends can be useful if an endpoint returns records of multiple classes, because it allows clients to determine the class of each result record.

The service guarantees that backends of all types can co-exist independently in the same directory, i.e., there are no name collisions in files that are used for different backends (as long as no class name starts with `.` or `_`)).

The following configuration snippet shows how to define a backend for a collection:

```yaml
...
collections:
  collection_with_default_record_dir+stl_backend:
    # This is a collection with the default backend, i.e. `record_dir+stl` and
    # the default authentication, i.e. config-based authentication.
    default_token: anon_read
    curated: collection_1/curated

  collection_with_forgejo_authentication_source:
    # This is a collection with the default backend, i.e. `record_dir+stl` and
    # a forgejo-based authentication source. That means it will use a forgejo
    # instance to determine the permissions of a token for this collection.
    # The instance is also used to determine the user-id and the incoming label.
    # In the case of forgejo, the user-id and the incoming label are the
    # forgejo login associated with the token.

    # We still need the name of a default token. If the token is defined in this
    # config file, its properties will be determined by the
    # config file. If the token is not defined in the config file, its
    # properties will be determined by the authentication sources. In this
    # example by the forgejo-instance at `https://forgejo.example.com`.
    # If there is more than one authentication source, they will be tried
    # in the order they are defined in the config file.
    default_token: anon_read    # We still need a default token
    curated: collection_2/curated

    # Token permissions, user-ids (for record annotations), and incoming
    # label can be determined by multiple authentication sources.
    # If no source is defined, `config` will be used, which reads token
    # information from the config file.
    # This example explicitly defines `config` and a second authentication
    # source, a `forgejo` authentication source.
    auth_sources:
      - type: forgejo   # requires `user`-read and `organization`-read permissions on token
        # The API-URL of the forgejo instance that should be used
        url: https://forgejo.example.com/api/v1
        # An organization
        organization: data_handling
        # A team in the organization. The authorization of the team
        # determines the permissions of the token
        team: data_entry_personal
        # `label_type` determines how an incoming label is created for
        # a Forgejo token. If `label_type` is `team`, the incoming label
        # will be `forgejo-team-<organization>-<team>`. If `label_type`
        # is `user`, the incoming label will be 
        # `forgejo-user-<user-login>`
        label_type: team
        # An optional repository. The token will only be authorized
        # if the team has access to the repository. Note: if `repo`
        # is set, the token must have at least repository read
        # permissions.
        repo: reference-repository

      # Fallback to the config file.
      - type: config    # check tokens from the configuration file

      # Multiple authorization sources are allowed. They will be tried in the
      # order defined in the config file. If an authorization source returns
      # permissions for a token, those permissions will be used and no other
      # authorization sources will be queried.
      # The default authorization source is `config`, which reads the token 
      # permissions, user-id, and incoming
  
  collection_with_explicit_record_dir+stl_backend:
    default_token: anon_read
    curated: collection_3/curated
    backend:
      # The record_dir-backend is identified by the
      # type: "record_dir". No more attributes are
      # defined for this backend.
      type: record_dir+stl

  collection_with_sqlite_backend:
    default_token: anon_read
    curated: collection_4/curated
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

The service provides the following user endpoints (in addition to user-endpoints there exist endpoints for curators, to view them check the `/docs`-path in an installed service):

- `POST /<collection>/record/<class>`: an object of type `<class>` (defined by the schema associated with `<collection>`) can be posted to this endpoint.
 It will be stored in the incoming area for this collection and the user defined by the provided token.
 In order to `POST` an object to the service, you MUST provide a valid token in the HTTP-header `X-DumpThings-Token` with write permissions.
 The endpoint supports the query parameter `format`, to select the format of the posted data.
 It can be set to `json` (the default) or to `ttl` (Terse RDF Triple Language, a.k.a. Turtle).
 If the `json`-format is selected, the content-type should be `application/json`.
 If the `ttl`-format is selected, the content-type should be `text/turtle`.  
 The service supports extraction of inlined records as described in [Dump Things Service](https://concepts.datalad.org/dump-things/).
 On success, the endpoint will return a list of all stored records.
 This might be more than one record if the posted object contains inlined records.

- `POST /<collection>/validate/record/<class>`: an object of type `<class>` (defined by the schema associated with `<collection>`) can be posted to this endpoint.
  It will validate the posted data.
  In order to `POST` an object to the service, you MUST provide a valid token in the HTTP-header `X-DumpThings-Token` with write permissions.
  The endpoint supports the query parameter `format`, to select the format of the posted data.
  It can be set to `json` (the default) or to `ttl` (Terse RDF Triple Language, a.k.a. Turtle).
  If the `json`-format is selected, the content-type should be `application/json`.
  If the `ttl`-format is selected, the content-type should be `text/turtle`.  
  The service supports extraction of inlined records as described in [Dump Things Service](https://concepts.datalad.org/dump-things/).
  On success, the endpoint will return a list of all stored records.
  This might be more than one record if the posted object contains inlined records.

- `GET /<collection>/records/<class>`: retrieve all readable objects from collection `<collection>` that are of type `<class>` or any of its subclasses.
 Objects are readable if the default token for the collection allows reading of objects or if a token is provided that allows reading of objects in the collection.
 Objects from incoming spaces will take precedence over objects from curated spaces, i.e. if there are two objects with identical `pid` in the curated space and in the incoming space, the object from the incoming space will be returned.
 The endpoint supports the query parameter `format`, which determines the format of the query result.
 It can be set to `json` (the default) or to `ttl`,
 The endpoint supports the query parameter `matching`, which is interpreted by `sqlite`-backends and ignored by `record_dir`-backends.
 If given, the endpoint will only return records for which the JSON-string representation matches the `matching` parameter.
 Matching supports the wildcard character `%` which matches any characters.
 For example, to search for `Alice` anywhere in the JSON-string representation of the record the matching parameter should be set to `%Alice%` or `%alice%` (matching is not case-sentitive).
 The result is a list of JSON-records or ttl-strings, depending on the selected format.

- `GET /<collection>/records/p/<class>`: this endpoint (ending on `.../p/<class>`) provides the same functionality as the endpoint `GET /<collection>/records/<class>` (without `.../p/...`) but supports result pagination. In addition to the query parameters `format` and `matching`, it supports the query parameters `page` and `size`.
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

- `GET /<collection>/record?pid=<pid>`: retrieve an object with the pid `<pid>` from the collection `<collection>`, if the provided token allows reading. If the provided token allows reading of incoming and curated spaces, objects from incoming spaces will take precedence.
  The endpoint supports the query parameter `format`, which determines the format of the query result.
  It can be set to `json` (the default) or to `ttl`,


- `GET /server`: this endpoint provides information about the server.
  The response is a JSON object with the following structure:
```json
{
  "version": "<version of the server>"
}
```


- `GET /<collection>/records/`:  retrieve all readable objects from collection `<collection>`.
  Objects are readable if the default token for the collection allows reading of objects or if a token is provided that allows reading of objects in the collection.
  Objects from incoming spaces will take precedence over objects from curated spaces, i.e. if there are two objects with identical `pid` in the curated space and in the incoming space, the object from the incoming space will be returned.
  The endpoint supports the query parameter `format`, which determines the format of the query result.
  It can be set to `json` (the default) or to `ttl`,
  The endpoint supports the query parameter `matching`, which is interpreted by `sqlite`-backends and ignored by `record_dir`-backends.
  If given, the endpoint will only return records for which the JSON-string representation matches the `matching` parameter.
  The result is a list of JSON-records or ttl-strings, depending on the selected format.


- `GET /<collection>/records/p/`: this endpoint (ending on `.../p/`) provides the same functionality as the endpoint `GET /<collection>/records/` (without `.../p/`) but supports result pagination. In addition to the query parameters `format` and `matching`, it supports the query parameters `page` and `size`.
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


- `DELETE /<collection>/record?pid=<pid>`: delete an object with the pid `<pid>` from the incoming area of the collection `<collection>`, if the provided token allows writing to the incoming area.
 The result is either `True` if the object was deleted or `False` if the object did not exists or was not deleted.


- `GET /docs`: provides information about the API of the service, i.e. about all endpoints.

#### Curation endpoints

The service support a set of curation-endpoints that give direct access to the curated area as well as to existing incoming areas.
This access requires a `CURATOR`-token.
Details about the curation-endpoints can be found in [this issue](https://github.com/christian-monch/dump-things-server/issues/118).


### Tips & Tricks


#### Using the same backend for incoming and curated areas

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

#### Migrating from `record_dir` (or `record_dir+stl`) to `sqlite`

The command `dump-things-copy-store` can be used to copy a collection from a `record_dir` (or `record_dir+stl`) store to a `sqlite` store.
The command expects a source and a destination store. Both are given in the format `<backend>:<directory-path>`, where `<backend>` is one of `record_dir`, `record_dir+stl`, `sqlite`, or `sqlite+stl`, and `<path>` is the path to the directory of the store.

For example, to migrate a collection from a `record_dir`-backend at the directory `<path-to-data>/penguis/curated` to a `sqlite` backend in the same directory, the following command can be used:
```bash
> dump-things-copy-store \
    record_dir:<path-to-data>/penguis/curated  \
    sqlite:<path-to-data>/penguis/curated
```

For example, to migrate from a `record_dir+stl` backend, the command is similar, but a schema has to be supplied via the `-s/--schema` command line parameter. For example:
```bash
> dump-things-copy-store \
    --schema https://concepts.inm7.de/s/flat-data/unreleased.yaml \
    record_dir+stl:<path-to-data>/penguis/curated  \
    sqlite:<path-to-data>/penguis/curated
```
(Note: a `record_dir:<path>` can be used to copy without the schema type layer from a `record_dir+stl` backend. But in this case the copied records will not have a `schema_type` attribute, because the `record_dir` backend does not "put it back in", unlike a `record_dir+stl` backend.)

If the source backend is a `record_dir` or `record_dir+stl` backend and the store was manually modified outside the service (for example, by adding or removing files), it is recommended to run the command `dump-things-rebuild-index` on the source store before copying. This ensures that the index is up to date and all records are copied.

If any backend is a `record_dir+stl` backend, a schema has to be supplied via the `-s/--schema` command line parameter. The schema is used to determine the `schema_type` attribute of the records that are copied.


### Maintenance commands

- `dump-things-rebuild-index`: this command rebuilds the persistent index of a `record_dir`store. This should be done after the `record_dir` store was modified outside the service, for example, by manually adding or removing files in the directory structure of the store.

- `dump-things-copy-store`: this command copies a collection that is stored in a source store to a destination store. For example, to copy a collection from a `record_dir` store at the directory `<path-to-data>/penguis/curated` to a `sqlite` store in the same directory, the following command can be used:
  ```bash
  > dump-things-copy-store \
      record_dir:<path-to-data>/penguis/curated  \
      sqlite:<path-to-data>/penguis/curated
  ```
  The copy command will add the copied records to any existing record in the destination store.
  Note: when records are copied from a `record-dir` store, the index is used to locate the records in the source store. If the index is not up-to-date, the copied records might not be complete. In this case, it is recommended to run `dump-things-rebuild-index` on the source store before copying.

- `dump-things-pid-check`: this command checks the pids in all collections of a store to verify that they can be resolved (if they are in CURIE form).
  This is useful to validate the proper definition of prefixes after schema-changes.

- `dump-things-create-merged-schema`: this command creates a new schema that statically contains all schemas that the original schema imported.
  The new schema is fully self contained and does not reference any other schemas anymore.

### If things go wrong

#### Delete a record manually

If a schema was changed, for example a prefix-definition changed, the service might not be able anymore to delete a record.
In this case the record can be deleted manually if you have access to the storage root.

To delete the record, open a shell and navigate (`cd`) to the directory where the store is located.
The location can be determined from the configuration file.
Depending on the storage backend, the next steps are different.

##### `record-dir` backend

Delete the record from disk by removing it, e.g. `rm -f <path-to-record>`

Run the command `dump-things-rebuild-index`

##### `sqlite` backend

Run the command:

```bash
> sqlite3 __sqlite-records.db
```

If you know the pid of the record you want to delete, enter the following on the prompt to delete the record with pid `some-pid`:

```sql
> delete from thing where json_extract(thing.object, '$.pid') = 'some-pid';
```

If you know the IRI of the record you want to delete, enter the following on the prompt to delete the record with IRI `some-iri`:

```sql
> delete from thing where iri = 'some-iri';
```



### Requirements

The service requires sqlite3.


## Acknowledgements

This work was funded, in part, by

- Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under grant TRR 379 (546006540, Q02 project)


- MKW-NRW: Ministerium für Kultur und Wissenschaft des Landes Nordrhein-Westfalen under the Kooperationsplattformen 2022 program, grant number: KP22-106A
