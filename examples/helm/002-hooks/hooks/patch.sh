#!/bin/bash
set -e
for p in patches.d/*
do
  echo "Patching $p ...";
  patch -d "$1" -p0 < $p
done