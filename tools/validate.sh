
if [ $# -ne 1 ]; then
  echo "Usage: $0 <record-collection-root-dir>" >&2
  exit 1
fi

pushd "$1"

schema_location="$(grep schema .dumpthings.yaml |cut -d ' ' -f 2)"

echo using schema $schema_location

tempdir=$(mktemp -d)
curl $schema_location -o $tempdir/schema.yaml

for directory in $(find . -maxdepth 1 -type d); do
  if [ $directory == "." ]; then
    continue
  fi

  for file in $(find $directory -type f); do
    class="$(echo $directory|cut -d '/' -f 2)"
    echo "Validating ``$class``-object in $file"
    linkml-validate -s $tempdir/schema.yaml --target-class $class $file
    linkml-convert -t ttl -s "$schema_location" --target-class $class $file
  done
done

rm -rf $tempdir

popd
