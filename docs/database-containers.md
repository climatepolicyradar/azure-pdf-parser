# Database containers

**Copied from [harrisonpim/biscuit-cutter](https://github.com/harrisonpim/biscuit-cutter)**

It's often useful to experiment with a local database before relying on cloud resources. Configuration for a couple of common database types is included here.

## Postgres

Adding the following service to your `docker-compose.yml` will make an postgres instance available on port 5432.

```yml
#docker-compose.yml
services:
  postgres:
    image: postgres
    restart: always
    env_file: .env
    ports:
      - 5432:5432
    volumes:
      - type: bind
        source: ./data/postgres
        target: /var/lib/postgresql/data/
```

with the following directories created to store (and persist) the data

```text
.
├── docker-compose.yml
└── data
    └── postgres
```

and the following in a root-level `.env` file

```shell
#.env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=database
```

## Elasticsearch

Adding the following service to your `docker-compose.yml` will make an elasticsearch instance available on port 9200. The kibana service included here is optional.

```yml
#docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.13.2
    volumes:
      - type: bind
        source: ./data/elasticsearch
        target: /usr/share/elasticsearch/data
    ports:
      - 9200:9200
    env_file: .env
    environment:
      discovery.type: single-node
      ES_JAVA_OPTS: -Xms3g -Xmx3g

  kibana:
    image: docker.elastic.co/kibana/kibana:7.13.2
    ports:
      - 5601:5601
    depends_on:
      - elasticsearch
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
```

with the following directories created to store (and persist) the data

```text
.
├── docker-compose.yml
└── data
    └── elasticsearch
```

and the following in a root-level `.env` file

```shell
#.env
ELASTIC_HOST=http://elasticsearch:9200
ELASTIC_USERNAME=elastic
ELASTIC_PASSWORD=changeme
```

## Neo4j

Adding the following service to your `docker-compose.yml` will make a neo4j instance available on port 7474, with APOC and graph data science plugins installed.

```yml
#docker-compose.yml
services:
  neo4j:
    image: neo4j:latest
    volumes:
      - type: bind
        source: ./data/neo4j/data
        target: /data
      - type: bind
        source: ./data/neo4j/logs
        target: /logs
    ports:
      - 7474:7474
      - 7687:7687
    env_file: .env
    environment:
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4JLABS_PLUGINS=["graph-data-science", "apoc"]
      - NEO4J_dbms_security_procedures_whitelist=gds.*, apoc.*
      - NEO4J_dbms_security_procedures_unrestricted=gds.*, apoc.*
```

with the following directories created to store (and persist) the data

```text
.
├── docker-compose.yml
└── data
    └── neo4j
        └── data
        └── logs
```

and the following in a root-level `.env` file

```shell
#.env
NEO4J_HOST=http://neo4j:7474
NEO4J_AUTH=neo4j/password
```
