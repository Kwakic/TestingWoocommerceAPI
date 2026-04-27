# 🧪 TestEcommerceAPI — API + Database Validation Framework

## 🔍 Overview

TestEcommerceAPI is a **Python-based API testing framework** designed for **end-to-end validation of e-commerce systems**, specifically WooCommerce.

Unlike typical API test suites, this framework validates:

* ✔ API responses (contract & business logic)
* ✔ Database state consistency (true source of truth)
* ✔ End-to-end workflows (create → update → delete → verify)

👉 The goal is **real integration testing**, not mocked or superficial checks.

---

## 🧱 Architecture

```
pytest
  ↓
Helpers (business logic)
  ↓
API Clients (REST layer)
  ↓
HTTP Client (transport)
  ↓
WooCommerce API
  ↓
MySQL Database (validated via DAO)
```

Key principles:

* Separation of concerns (API / Helpers / DAO / Validators)
* Stateless API clients
* Schema validation + DB verification
* Structured logging + Allure reporting

---

## 🚀 Quick Start (1 command)

### Requirements

* Docker
* docker-compose
* Python 3.13+

### Run everything:

```bash
make run
```

---

## ⚙️ Manual Setup (if not using Make)

### 1. Start environment

```bash
docker compose -f docker-compose.wp.yml up -d
```

### 2. Install dependencies

```bash
pip install -e .
pip install -r requirements.txt
```

### 3. Run tests

```bash
pytest -v
```

---

## 🧪 What is tested?

### ✔ Customers API

* Create customer
* Update customer
* Delete customer
* Filtering & retrieval
* Error handling

### ✔ Database validation

* Data persistence
* Soft delete behavior
* Timestamp consistency (API vs DB)
* Business rules enforcement

---

## 📊 Reporting

All tests generate:

* Structured logs (JSON)
* Allure reports

```bash
allure serve reports/allure-results
```

---

## 🧠 Why this project?

Most API test suites validate only HTTP responses.

This framework goes further:

```text
API is validated against the database
```

👉 Ensures:

* No hidden data inconsistencies
* Real business correctness
* Production-like validation

---

## ⚠️ Notes

* Tests run against a **local Dockerized WooCommerce instance**
* No external services or credentials required
* Data is created dynamically and cleaned automatically

---

## 🧑‍💻 Author

Designed as a **production-style API testing framework** for learning, showcasing, and interview discussions.
