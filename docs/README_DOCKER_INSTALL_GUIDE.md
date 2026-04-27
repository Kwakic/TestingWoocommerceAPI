# 🔥 COMMANDS FOR DOCKER

---

## 📚 Common Columns in the Output
When you run these commands, you will see a table with several key details for each container:

* CONTAINER ID: A unique identifier for the container.
* IMAGE: The image used to create the container.
* COMMAND: The executable that ran when the container started.
* STATUS: Whether the container is "Up" (running), "Exited" (stopped), or "Paused".
* NAMES: The human-readable name assigned to the container.

To create:
```Bash
docker compose -f docker-compose.wp.yml up -d
```

---

To clean it:
```Bash
docker compose -f docker-compose.wp.yml down -v
```
---
List running containers ONLY:
```Bash
docker ps
# OR
docker container ls
```
---

Show only container IDs:
```Bash
docker ps -q
```
👉 useful for scripts

---

List ALL containers (running and stopped)
```Bash
docker ps -a
 # OR
docker container ls -
```
---
Show file size of containers:

```Bash
docker ps -s
```

---
Show the latest created container:
```Bash
docker ps -l
```
---

## 🚀 Advanced Viewing Options
If you need specific information, you can use these additional flags:

* Prevent text truncation: Use `--no-trunc` to see the full, unshortened container IDs and commands.
* Custom formatting: Use `--format` to only show specific columns, such as just the names:
`docker ps --format "{{.Names}}"`.
* Filtering results: Use -f to filter by specific criteria, such as status:
`docker ps -f "status=exited"`.
---

## 🧹 Clean reset (mandatory)


```
docker compose -f docker-compose.wp.yml down -v
rm -rf wp-data
```
👉 This removes broken Docker volume + resets filesystem

---

```Bash
rm -rf woocommerce
```
👉 This removes existing plugin cleanly

---

## 🧠 Translation to real-world value

What you just built is NOT:
```
"just Docker"
```

This is:

```
✔ Self-contained test environment
✔ Fully reproducible system
✔ Zero manual setup
✔ API + DB + tests wired together
```
👉 This is enterprise-level QA setup

---
## 🧩 The FULL FLOW (now real, not theoretical)
### 1️⃣ make run
```Bash
make run
```

Triggers:
```
Makefile → docker-compose → setup.sh → pytest
```
---
### 2️⃣ Docker boots infra
```
wc-db  → MySQL
wc-wp  → WordPress
wc-cli → WP CLI executor
```
👉 This is your infra layer

---

### 3️⃣ setup.sh configures system

Step by step:
```
1. Wait for containers
2. Fix permissions (critical for plugins)
3. Install WordPress
4. Install WooCommerce
5. Activate plugin
6. Generate API keys
```
👉 This is your environment bootstrap layer

---
### 4️⃣ Your framework kicks in

```
pytest → fixtures → API clients → DB validators
```
Using:

* your HTTPClient
* your CustomersApi
* your DB DAO
* your validators

👉 This is your test framework layer

---
### 5️⃣ Tests run against REAL system
```
API → http://localhost:8888/wp-json/wc/v3/
DB  → MySQL container
```
👉 This is true integration testing

---

## 💼 Interview-level impact (this is important)

What you now have is something you can say:

`"I built a fully reproducible API testing framework with Dockerized infrastructure,
automated environment provisioning, and DB-level validation."`

```

```


```

```


```

```


```

```
