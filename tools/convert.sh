
if [ $# -ne 1 ]; then
  echo "Usage: $0 <record-collection-root-dir>" >&2
  exit 1
fi

pushd $1

schema_location="$(grep schema .dumpthings.yaml |cut -d ' ' -f 2)"

echo using schema $schema_location
echo echo $schema_location | grep '^http[s]*://' >/dev/null

if [ $? -ne 0 ]; then
  schema=$schema_location
else
  tempdir=$(mktemp -d)
  schema=$tempdir/schema.yaml
  curl $schema_location -o $schema
fi

for directory in $(find . -maxdepth 1 -type d); do
  if [ $directory == "." ]; then
    continue
  fi

  for file in $(find $directory -type f); do
    class="$(echo $directory|cut -d '/' -f 2)"
    echo "Converting ``$class``-object in $file to ttl"
    linkml-convert -t ttl -s "$schema" -C $class $file
  done
done

popd
