#!/bin/sh
set -eu

dataset_dir="data/raw/ohsome_peru_road_history_pilot"
endpoint="https://api.ohsome.org/v1/elements/geometry"
bbox="-72.31522443113718,-16.85816825597201,-71.58236420195395,-16.135677662346303"

mkdir -p "$dataset_dir"

for year in 2015 2024; do
  destination="$dataset_dir/osm_highways_${year}-01-01.geojson"
  curl --fail --silent --show-error -X POST "$endpoint" \
    --data-urlencode "bboxes=$bbox" \
    --data-urlencode "time=${year}-01-01" \
    --data-urlencode 'filter=highway=* and type:way' \
    --data-urlencode 'properties=tags,metadata' \
    --data-urlencode 'clipGeometry=true' \
    --output "$destination"
  shasum -a 256 "$destination" > "$destination.sha256"
done

