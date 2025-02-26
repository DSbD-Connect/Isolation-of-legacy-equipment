#!/bin/bash

# need smbclient installed on server also

# build the image
docker build -t apache-php-mod_authnz_external . --network=host
# --network=host allows the "apt-get" command run during build to access the internet

# prepare directories for the auth programs
mkdir cheri-auth_prog nocheri-auth_prog
cp password cheri-auth_prog
cp password nocheri-auth_prog

# compile the auth programs
source /morello/env/morello-sdk
clang -march=morello --target=aarch64-linux-musl_purecap --sysroot=${MUSL_HOME} auth.c -o cheri-auth_prog/auth -static
clang --target=aarch64-linux-gnu --sysroot=/root/musl-aarch64/musl-install auth.c -o nocheri-auth_prog/auth -static

