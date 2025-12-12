

### poly1.yaml		yaml->ttl

| Class in File | Class Specified | Class Resulting |
|---------------|-----------------|-----------------|
| ORCID | ORCID           | ORCID           |
| ORCID | Identifier      | ORCID           |
| ORCID | -               | [Error -C]      |


###	poly1.ttl	ttl->yaml

| Class in File | Class Specified | Class Resulting |
|---------------|-----------------|-----------------|
| ORCID | ORCID           | ORCID           |
| ORCID | Identifier      | ORCID           |
| ORCID | -               | [Error -C]      |


### poly2.yaml		yaml->ttl

| Class in "identifiers" | Class Specified | Class Resulting in "identifiers" |
|-----------------------|-----------------|----------------------------------|
| ORCID                 | XYZPerson       | ORCID                            |
| ORCID                 | -               | [Error -C]                       |


### poly2.ttl		ttl->yaml

| Class in "identifiers" | Class Specified | Class Resulting in "identifiers"     |
|-----------------------|-----------------|--------------------------------------|
| ORCID                 | XYZPerson       | [Error unexpected:  'schema_agency') |
| ORCID                 | -               | [Error -C]                           |

