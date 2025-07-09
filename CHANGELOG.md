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
  This version adds a new backend, `sqllite`, which uses a SQLite database. More
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
