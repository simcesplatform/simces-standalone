# Docker configuration for MongoDB

## Configuration

By default the installed version of MongoDB is 4.2.7. This can be changed by modifying [`docker-compose-mongo.yml`](docker-compose-mongo.yml).

- [`mongodb.env`](mongodb.env)
    - `MONGO_INITDB_ROOT_USERNAME`
        - The username for the root user.
    - `MONGO_INITDB_ROOT_PASSWORD`
        - The password for the root user.
- [`mongo-express.env`](mongo-express.env)
    - `ME_CONFIG_MONGODB_ADMINUSERNAME`
        - The username for the database root user. Should be the same as in `mongodb.env`.
    - `ME_CONFIG_MONGODB_ADMINPASSWORD`
        - The password for the database root user. Should be the same as in `mongodb.env`.
    - `ME_CONFIG_BASICAUTH_USERNAME`
        - The username for the mongo-express web page.
    - `ME_CONFIG_BASICAUTH_PASSWORD`
        - The password for the mongo-express web page.

To prevent any local changes made to the configuration files showing with `git status`:

```bash
git update-index --skip-worktree mongodb.env mongo-express.env
```

## Install

The first line is only required if the `mongodb_network` does not exist.

```bash
docker network create mongodb_network
docker-compose -f docker-compose-mongo.yml up --detach
```

- Mongo Express with admin privileges will be available at [http://localhost:8081](http://localhost:8081)
- MongoDB will be available at [http://mongodb:27017](http://mongodb:27017) but only for Docker containers that are also in the same Docker network, `mongodb_network`.

## Access MongoDB using the Mongo shell

```bash
docker exec -it mongodb mongo --username <MONGO_ROOT_USERNAME>
```

Tutorial for the Mongo shell: [https://docs.mongodb.com/manual/tutorial/getting-started/](https://docs.mongodb.com/manual/tutorial/getting-started/)

## Uninstall

```bash
docker-compose -f docker-compose-mongo.yml down --remove-orphans
```

## Remove MongoDB data

```bash
docker volume rm mongodb_data
```
