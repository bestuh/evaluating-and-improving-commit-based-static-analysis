# Setup
Create a `data` directory and place an SQL dump in it (e.q. `cve_mappings.sql`). The mysql database will then be initialized with the dump.
Then run `docker compose up -d` to start the database and phpMyAdmin.

# Login to phpMyAdmin
PhpMyAdmin can be accessed at [localhost:8080](http://localhost:8080/index.php).
Credentials are as follows:
-  **Server**: `<mysql-db-container-ip>`:3306
-  **Username**: root
-  **Password**: password

> Note: You can get the `<mysql-db-container-ip>` via `docker inspect mysql-db | grep IPAddress`.

> Note: First start can take some time (~15min) due to import of data.