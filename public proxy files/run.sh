#!/bin/bash

docker rm -f medical-image-demo-nocheri 1> /dev/null 2> /dev/null
docker rm -f medical-image-demo-cheri 1> /dev/null 2> /dev/null

docker create --name medical-image-demo-nocheri \
    --network=host \
    -v "$PWD/html":/var/www/html \
    apache-php-mod_authnz_external
docker cp nocheri-000-default.conf \
       medical-image-demo-nocheri:/etc/apache2/sites-available/000-default.conf
docker cp nocheri-ports.conf \
       medical-image-demo-nocheri:/etc/apache2/ports.conf
docker cp nocheri-auth_prog  \
       medical-image-demo-nocheri:/etc/apache2/auth_prog

docker create --name medical-image-demo-cheri \
    --network=host \
    -v "$PWD/html":/var/www/html \
    apache-php-mod_authnz_external
docker cp cheri-000-default.conf \
       medical-image-demo-cheri:/etc/apache2/sites-available/000-default.conf
docker cp cheri-ports.conf \
       medical-image-demo-cheri:/etc/apache2/ports.conf
docker cp cheri-auth_prog  \
       medical-image-demo-cheri:/etc/apache2/auth_prog

docker start medical-image-demo-nocheri
docker start medical-image-demo-cheri
    
while [ 1 ]
do
./smb-sync.py
sleep 20
done


