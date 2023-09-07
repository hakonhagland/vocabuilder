#! /bin/bash

if (( $# != 1 )); then
    echo "Usage: $0 <dockerdir>"
    exit 1
fi
dockerdir="$1"
#dir=$(mktemp -d)
dir="$dockerdir"
fn="myapp.tar.gz"
path="$dir"/myapp.tar.gz   # docker requires the file to be in the build context, so we put it there
# create a tar.gz archive of the current git HEAD that respects .gitignore
git archive -o "$path" --format=tar.gz HEAD
# pass the archive file to docker build as a build argument
docker build --build-arg "GIT_ARCH=$fn" -t python-vocabuilder "$dockerdir"
rm "$path" # remove the archive file
