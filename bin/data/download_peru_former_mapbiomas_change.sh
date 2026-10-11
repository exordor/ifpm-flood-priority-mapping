#!/bin/sh
set -eu

dataset_dir="data/raw/mapbiomas_peru_collection3_peru_former"
base_url="https://storage.googleapis.com/mapbiomas-public/initiatives/peru/collection_3/LULC"

mkdir -p "$dataset_dir"

for year in 2014 2015 2016 2022 2023 2024; do
  filename="peru_collection3_integration_v1-classification_${year}.tif"
  destination="$dataset_dir/$filename"
  curl --fail --location --continue-at - \
    --output "$destination" \
    "$base_url/$filename"
  shasum -a 256 "$destination" > "$destination.sha256"
done
