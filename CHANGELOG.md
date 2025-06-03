# 0.1.0 (2025-06-03)

## New features

  - report full path in records with colliding PIDs-exception
  - don't exit if PID collision is detected at startup, but log an error
  - add a changelog
  - improve resilience of record directory stores against fault YAML content and non-yaml files 
  - omit creation of unused record directory stores


# 0.0.1

## Features

  - add in-memory PID-index for record directory stores
  - add token capability endpoint (`/<collection>/token_permissions`)
  - update configuration to allow details directory specification for tokens and incoming directories
