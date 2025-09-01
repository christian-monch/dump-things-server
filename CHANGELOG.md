# 2.3.2 (2025-09-01)

# Bugfixes

- This version improves the bugfix that was introduced in version 2.3.1.
  A token provided for a collection that is not defined in the token
  configuration object will now be ignored.


# 2.3.1 (2025-09-01)

# Bugfixes

- Fix a bug that caused internal server errors if a token was provided for a
  collection that was not defined in the token configuration object. Now, this
  situation will lead to a 401 Unauthorized error.  
  (There is no ignoring of the token and no fallback to a default token. To
  use a default token, the request should be performed without a token.)


# 2.3.0 (2025-09-01)

## New features

- Support explicit type declarations in TTL input for all types that are
  defined in the underlying schema.


# 2.2.0 (2025-08-29)

## New features

- Add a `x-dumpthings-service-version`-header to all API responses. This header
  contains the version of the dump-things-service that generated the response.

## Bugfixes

- Fix a bug in matching-parameter handling that prevented class-selection.


# 2.1.0 (2025-08-28)

## New features

- Add a `matching`-parameter to the `/<collection>/records/<class>`- and
  `/<collection>/records/p/<class>`-endpoint.
  This parameter allows to filter records by a simple text matching.


# 2.0.1 (2025-07-24)

## Bugfixes

- Ensure that format conversion errors are caught and reported correctly in
  the API.


# 2.0.0 (2025-07-15)

## Breaking changes

- The `--export-to` command line parameter was removed from
  `dump-things-service`. It is replaced with the functionally identical command
  line parameter `--export-json`.

- The `--sort-by` command line parameter was removed from `dump-things-service`.
  The reason is that sorting key modification requires rebuilding of the
  `record_dir` indices. That would defeat the purpose of the persistent
  `record_dir` index, which is fast startup. All results are now sorted by the
  `pid` field by default.

- The backend that was previously called `record_dir` is now called
  `record_dir+stl`.
  `record_dir+stl` is now the default backend. It is functionally identical to
  the previous `record_dir`-backend. Changes in configuration files are only
  required if the `record_dir` backend was explicitly defined in the
  configuration file.

## New features

- Factor out a Schema Type Layer (STL) from the `record_dir` backend." The STL
  can be used with every backend. It removes top-level `schema_type`-entries
  from records before they are stored. It also adds the correct top-level
  `schema_type`-entry to records that are read from a store. This functionality 
  was previously built into the `record_dir` backend. Now it can be combined
  with `record_dir` and `sqlite` backends.

- Add the backend extension `stl` which specifies that a backend should be used
  with the STL. For example `record_dir+stl` defines a backend that uses
  `record_dir` with the STL on top.

- The command `dump-things-copy-store` was added. It copies a data store from 
  one backend to another. This is useful for migrating to a different backend,
  for example, from the `record_dir` backend to the `sqlite` backend.

- The command `dump-things-rebuild-index` was added. It allows rebuilding the
  index of a `record_dir` data store, after the store was modified externally.


# 1.1.0 (2025-07-10)

## New features

- Add a `--export-tree` command line parameter to the `dump-things-service` command.
  This parameter allows to export a data store to tree structure as described
  [here](https://concepts.datalad.org/dump-things/).

## Bugfixes

- Fix a typo in the "tips and tricks" section of the README.md file.


# 1.0.0 (2025-07-09)

## Breaking changes

- The result of `/<collection>/records/<class>`-endpoint for the output format
  TTL has changed its structure. It is now a JSON array where the individual
  entries are strings. Each entry is a TTL document that describes a single record.
  Earlier versions would return a single TTL document that contained all records.
  Due to the high computational cost of combining multiple TTL documents into a
  single document, this change was made. In addition, this change unified the
  code used in the paginated and the non-paginated endpoints.

## New features

- support for multiple backends. The default backend is `record_dir`, which is the
  backend used in the previous versions. It is fully compatible with existing stores.
  This version adds a new backend, `sqlite`, which uses a SQLite database. More
  SQL backends will be added in the future. SQL backends should be able to support
  far bigger record numbers than the `record_dir` backend (hundreds of thousands)
  without performance degradation.

- an export method has been added. With the command line parameter `--export`,
  the service exports all records of a data store and the schema information of
  collections to a JSON file or to stdout.


# 0.5.0 (2025-06-27)

## New features

- support sorting of result record lists. By default, result records are sorted by
  the field `pid`. The parameter `--sort-by` allows to define alternative fields
  for sorting. Multiple fields can be specified by repeating the `--sort-by` parameter.


# 0.4.0 (2025-06-25)

## New features

- limit the number of records that are returned via the `/<collection>/records/<class>`-endpoint.
 The maximum number of JSON-records is 1200, the maximum number of TTL-records is 60 (due to the high cost of combining TTL-records).
 An HTTP 413 error is returned if the number of records is exceeded.
 This limits backward compatibility, as the previous behavior was to return all records.

## Bugfixes

- fix errors in README.md


# 0.3.0 (2025-06-25)

## New features

- pagination support for class instance retrieval. To keep backward-compatibility  a new endpoint is added, i.e., `/<collection>/records/p/<class>`.

## Cleanup

- the datalad-concepts submodule was removed
- any calls to patch via post-install script were removed


# 0.2.7 (2025-06-24)

## Bugfixes

- monkeypatching was not triggered earlier, this is fixed now.

## Cleanup

- the datalad-concepts submodule was removed
- any calls to patch via post-install script were removed


# 0.2.6 (2025-06-22)

## Bugfixes

- ensure that the version number if correct


# 0.2.5 (2025-06-22)

## New feature

- dump-things-service does now patch its environment as required. There is no more
  need to provide a patched linkml-environment.
- the distribution package is now smaller, it does not contain the test directory anymore.

## Bugfixes

- ensure that non-existing collections are properly reported in unauthenticated requests


# 0.2.4 (2025-06-07)

## Bugfixes

- add missing entry point for `dump-things-service`-command.


# 0.2.3 (2025-06-06)

## Bugfixes

 - bump the version to 0.2.3


# 0.2.2 (2025-06-06)

## Bugfixes

 - describe the pypi-installation and start of the service in the README


# 0.2.1 (2025-06-05)

## New feature

 - dump-things-service is now available via pypi.
 - add `dump-things-service` command. This command can be used after installation to start the service


# 0.2.0 (2025-06-04)

## New features
  
  - set `schema_type`-attribute in all JSON records that are returned when storing or retrieving records
  - add mapping functions with 2-stage directory hierarchies: `digest_md5_p3_p3` and `digest_sha1_p3_p3`.
  - move all dependency definitions into `pyproject.toml`, remove `requirements.txt` and `requirements-devel.txt`


# 0.1.1 (2025-06-03)

## Bugfixes

  - fix a logging call in dynamically created code

# 0.1.0 (2025-06-03)

## New features

  - improve logging, add a --log-level command line parameter
  - report full path in records with colliding PIDs-exception
  - don't exit if PID collision is detected at startup, but log an error
  - add a changelog
  - improve resilience of record directory stores against fault YAML content and non-yaml files 
  - omit creation of unused record directory stores


# 0.0.1

## Features

  - add in-memory PID-index for record directory stores
  - add --error-mode command line parameter which allows the service to report a critical error on all endpoints
  - add token capability endpoint (`/<collection>/token_permissions`)
  - update configuration to allow details directory specification for tokens and incoming directories
