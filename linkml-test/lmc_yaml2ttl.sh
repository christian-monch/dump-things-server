#!/usr/bin/env bash

linkml-convert -t ttl -s "https://concepts.datalad.org/s/demo-rse-group/unreleased.yaml" -C $1 $2
