# 0.2.0 (2025-07-04)

## New features
  
  - set `schema_type`-attribute in all JSON records that are returned when storing or retrieving records
  - add mapping functions with 2-stage directory hierarchies: `digest_md5_p3_p3` and `digest_sha1_p3_p3`.
  - move all dependency definitions into `pyproject.toml`, remove `requirements.txt` and `requirements-devel.txt`


# 0.1.1 (2025-07-03)

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
