# Logify - Log Analysis Platform

## Overview

Logify is a FastAPI-based web application that analyzes log files and provides useful insights through a modern dashboard.

The application allows users to upload log files, stores analysis results in PostgreSQL, visualizes statistics using charts, and supports exporting reports.

---

## Features

- Upload log files
- Parse INFO, WARNING and ERROR logs
- Group similar errors
- Dashboard with statistics
- Chart.js visualization
- Search uploads
- Pagination
- Export as CSV
- Export as PDF
- Delete uploads
- User Authentication
- PostgreSQL Database
- Apache Reverse Proxy
- Systemd Service
- SELinux Compatible
- Responsive UI

---

## Technologies Used

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- HTML
- CSS
- JavaScript
- Chart.js
- Apache HTTP Server
- Systemd
- SELinux
- RHEL 10

---

## Project Structure

```
log-analyzer/
│
├── app/
├── uploads/
├── static/
├── templates/
├── requirements.txt
└── README.md
```

---

## Installation

```bash
git clone https://github.com/DivyaS-45/log-analyzer.git
cd log-analyzer

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## Screenshots

(Add dashboard screenshots here)

---

## Author

Divya Salvi
