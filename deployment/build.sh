#!/usr/bin/env bash

echo "------------------------------------------------------------------------------"
echo "Elasticsearch consumer Function"
echo "------------------------------------------------------------------------------"

echo "Building Elasticsearch Consumer function"
cd "$source_dir/consumers/elastic" || exit 1

[ -e dist ] && rm -r dist
mkdir -p dist
[ -e package ] && rm -r package
mkdir -p package
echo "preparing packages from requirements.txt"
# Package dependencies listed in requirements.txt
pushd package || exit 1
# Handle distutils install errors with setup.cfg
touch ./setup.cfg
echo "[install]" > ./setup.cfg
echo "prefix= " >> ./setup.cfg
# Try and handle failure if pip version mismatch
if [ -x "$(command -v pip)" ]; then
  pip install --quiet -r ../requirements.txt --target .
elif [ -x "$(command -v pip3)" ]; then
  echo "pip not found, trying with pip3"
  pip3 install --quiet -r ../requirements.txt --target .
elif ! [ -x "$(command -v pip)" ] && ! [ -x "$(command -v pip3)" ]; then
  echo "No version of pip installed. This script requires pip. Cleaning up and exiting."
  exit 1
fi
zip -q -r9 ../dist/esconsumer.zip .
popd || exit 1

zip -q -g dist/esconsumer.zip ./*.py
cp "./dist/esconsumer.zip" "$dist_dir/esconsumer.zip"