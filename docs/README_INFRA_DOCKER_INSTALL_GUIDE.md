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


---

# 🧠 What “infra” means in your case

In your project, infra (infrastructure) = everything that makes your system run, but is NOT your test logic.

In your repo, infra:

```
✔ docker-compose.wp.yml      → spins up DB + WordPress
✔ scripts/setup.sh           → installs WP + WooCommerce
✔ Makefile                   → orchestrates everything
✔ .env                       → configuration
✔ Dockerfile                 → environment definition
```

NOT infra (this is your framework):

```
✔ EcommerceAPI/
✔ helpers / API / DAO / validators
✔ pytest tests
```

### 👉 So clean separation is:

```
Framework → HOW to test
Infra     → WHERE to test
```

---

## 🧠 Big picture (your project in ONE sentence)

```
You built a testing ENGINE (framework) + a TEST ENVIRONMENT (Docker + WP)
```
👉 Those are two different things.

---

## 🧩 Your repo = 2 systems working together
### 1️⃣ The Framework (EcommerceAPI)

From your docs:

* layered architecture
* API → helper → DAO → validation

👉 This is:

```
HOW tests are executed
```
---

## 2️⃣ The Environment (Docker + WordPress)

From your README:
```
Tests run against a local Dockerized WooCommerce instance :contentReference[oaicite:1]{index=1}
```
👉 This is:
```
WHERE tests are executed
```
---

## 🔥 This is the missing link you didn’t have

Before:

```
You = developer
Your machine = environment
```
So everything “just worked”.

---
Now you want:

```
ANYONE → clone repo → run tests
```
👉 That requires:

```
Environment must be CREATED automatically
```

---
## ⚙️ So what is the flow REALLY?

Let’s simulate a random user (this is key).

---

## 🚀 🔁 FULL FLOW (REAL, step-by-step)

👤 User clones your repo

```bash
git clone ...
cd TestEcommerceAPI
```
### 🟡 Step 1 — Makefile (ENTRYPOINT)
User runs:

```bash
make run
```
👉 This is just a shortcut:
```
run: up setup test
```
👉 So internally:

---

### 🔵 Step 2 — Docker starts environment
```bash
docker compose up -d
```
👉 This creates:

```
✔ MySQL database
✔ WordPress server
✔ wp-cli container
```
At this moment:

```
❌ WordPress NOT installed yet
❌ WooCommerce NOT installed
❌ API NOT usable
```
---
### 🔴 Step 3 — setup.sh (THIS IS THE MAGIC)

This is what you were missing before.
```bash
scripts/setup.sh
```
👉 It does:

### 3.1 Install WordPress

```
wp core install
```
Now:
```
✔ WordPress exists
❌ WooCommerce still missing
```
---

### 3.2 Install WooCommerce
```bash
wp plugin install woocommerce --activate
```
Now:
```
✔ WooCommerce installed
✔ REST API enabled
```
---

### 3.3 Create API keys

```
✔ consumer_key
✔ consumer_secret
```
Now:
```
✔ API is usable
```

---

### 🟢 Step 4 — pytest runs

```Bash
pytest
```
Now your framework kicks in:

From your architecture:
```
pytest
 ↓
helpers
 ↓
API client
 ↓
WooCommerce API
 ↓
DB validation
```

---

### 🟣 Step 5 — DB validation

This is your special sauce:

```
✔ API response validated
✔ DB state validated
```

---

## 🎯 Why setup.sh exists

Without it:


```
Docker gives you EMPTY WordPress
```
👉 Tests fail:
```
401 / 403 / no data
```
With setup.sh:
```
Docker → fully configured WooCommerce
```
👉 Tests work

---

## 🎯 Why Makefile exists

Without Makefile:

User must run:

```Bash
docker compose up -d
bash scripts/setup.sh
pytest
```
👉 That’s error-prone

---

With Makefile:

```Bash
make run
```
👉 One command = clean UX

---

## 🧠 Where your other files fit

---

### 🟡 pyproject.toml

From your doc:

```
Defines packaging + pytest config :contentReference[oaicite:3]{index=3}
```
👉 Used when:


```Bash
pytest
pip install -e EcommerceAPI
```

---

### 🟡 pytest.ini

👉 Controls:

```
✔ test discovery
✔ markers
✔ logging
```

---
### 🟡 .env

👉 Used by:

```
✔ auth config
✔ API URL
✔ flags
```

---

## 🧠 Mental model you should keep
Think like this:

```
Framework = brain
Docker = body
setup.sh = birth process
Makefile = remote control
```

---

## 🔥 Final simplified flow

```
User
 ↓
make run
 ↓
Docker → creates empty system
 ↓
setup.sh → configures system
 ↓
pytest → runs your framework
 ↓
API + DB validated
```

---
## 🧠 Big architectural insight

You now clearly see separation:
```
setup.sh        → infrastructure
Makefile        → orchestration
pyproject.toml  → package definition
pip install     → package activation
pytest          → execution
```


---

## 🧠 Big picture (what you’ve built)

You now have:
```
Infra layer     → Docker (WordPress + DB)
Bootstrap       → setup.sh
Framework       → API + validators + helpers
Execution       → pytest
Reporting       → Allure + logs
CI              → GitHub Actions
```


👉 This is real SDET-level architecture

---

## 🧠 Final architecture (now correct)
```
User
 → make run
    → Docker (infra)
    → setup.sh (bootstrap)
    → pip install (framework)
    → pytest (tests)
    → Allure (report)
```

---

# 🐳 Your current architecture (important)

From your README:

* `docker-compose.wp.yml` spins:
  * MySQL
  * WordPress
  * WP-CLI

👉 This is already perfect for CI

---

## ❌ Do you need a Dockerfile?
### Answer: NO (for now)

You only need a `Dockerfile` if:

* you want to run tests inside a container
* or build a custom test image

👉 But you are doing:
```
GitHub runner (Ubuntu)
    ↓
runs docker-compose
    ↓
runs pytest locally
```
 ✔️This is simpler

 ✔️This is standard

 ✔️This is what you want

---

## ❌ Do you need .dockerignore?
### Answer: NO (for CI step)

Only needed if:

* you build Docker images (docker build)

👉 You are NOT building images → ignore it.

---

## 🧱 Core Docker concepts (simple but precise)
### 1. Image
* blueprint (like a class)
* e.g.:
  * mysql:8
  * wordpress:latest
---
### 2. Container
* running instance of an image (like an object)

---

### 3. Dockerfile
* how to build your own image

---

### 4. docker-compose
* orchestrates multiple containers

---

## 🔍 What YOUR docker-compose.wp.yml is doing

Most likely (based on your README):
```
services:
  db:
    image: mysql:8

  wordpress:
    image: wordpress:latest

  wpcli:
    image: wordpress:cli
```
👉 That means:

| Component | Source         |
| --------- | -------------- |
| MySQL     | prebuilt image |
| WordPress | prebuilt image |
| WP-CLI    | prebuilt image |

### ✅ So answer to your question:

> Does it create an image?

👉 ❌ No (in your case)

👉 ✔ It pulls existing images and runs containers

---

## 🧠 When DO you need a Dockerfile?

You need it only if:

### Case 1 — Custom test environment

Example:
```
FROM python:3.13
COPY . /app
RUN pip install -r requirements.txt
CMD ["pytest"]
```
👉 Then you run:

```
docker build -t test-runner .
docker run test-runner
```

---

## Case 2 — Full isolation (advanced CI)

Everything runs inside containers:

```
[ test container ]
        ↓
[ wordpress container ]
        ↓
[ mysql container ]
```

---

## ⚖️ Best Practice (for YOU)

You are here:

> QA / API testing / WooCommerce

👉 Best practice:

### ✅️ Use docker-compose for SYSTEM
### ✅ Run pytest on host (CI runner)

---

### 💡 Why this is better

| Approach                  | Pros               | Cons                |
| ------------------------- | ------------------ | ------------------- |
| pytest on host (your way) | simple, debuggable | slight env coupling |
| pytest in container       | reproducible       | harder debugging    |


```

```


```

```

```

```


```

```


```

```


```

```


```

```


```

```
