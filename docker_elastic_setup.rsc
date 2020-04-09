## Work on Linux
sudo sysctl -w vm.max_map_count=262144
#mkdir esdatadir
#chmod g+rwx esdatadir
#chgrp 0 esdatadir
sudo docker run -d -p 9200:9200 -p 9300:9300  -e "discovery.type=single-node" -e ES_JAVA_OPTS="-Xms8g -Xmx8g" elasticsearch:7.6.1

