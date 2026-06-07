# Interstellar Logistics Manager

An application for managing complex interstellar logistics, tracking ships, crew, cargo, routes, and telemetry data. This project demonstrates advanced MongoDB features such as aggregations, multi-document transactions, and Change Streams, ensuring operational atomicity and real-time updates.

## Table of Contents

1.  [Project Description](#1-project-description)
2.  [Application Features](#2-application-features)
3.  [Technologies Used](#3-technologies-used)
4.  [Prerequisites](#4-prerequisites)
5.  [Configuration and Launch](#5-configuration-and-launch)
    *   [Important Note: MongoDB Replica Set](#important-note-mongodb-replica-set)
    *   [Project File Preparation](#project-file-preparation)
    *   [Starting MongoDB Replica Set (First Time or After Shutdown)](#starting-mongodb-replica-set-first-time-or-after-shutdown)
    *   [Seeding Data](#seeding-data)
    *   [Launching the Flask Application](#launching-the-flask-application)
6.  [Using the Application](#6-using-the-application)
7.  [Troubleshooting](#7-troubleshooting)

---

## 1. Project Description

Interstellar Logistics Manager is a backend-first demonstration web application built with Python using the Flask framework. It is designed to manage complex logistics data in a fictional space universe. The application allows tracking of ships, crew, cargo, routes, and telemetry data, and provides advanced tools for data analysis and interaction.

## 2. Application Features

*   **Fleet Management:** Create, view, and update ship statuses and systems.
*   **Cargo Management:** Add and remove cargo from ships (using embedded documents).
*   **Crew Management:** List, create, update medical status of crew members, and assign them to ships.
*   **Routes:** View predefined space routes.
*   **Telemetry:** Add and retrieve telemetry readings from ships.
*   **Analytics:** Complex data reports and aggregations (e.g., fleet summary, critical missions, cargo breakdown, average telemetry parameters).
*   **Multi-Document Transactions:** Atomic operations modifying multiple documents (e.g., transferring a crew member between ships).
*   **Change Streams (Real-time Updates):** Instantly push database changes to the frontend.

## 3. Technologies Used

*   **Backend:** Python 3.x, Flask, PyMongo.
*   **Database:** MongoDB Server (NoSQL, document-oriented).
*   **Frontend:** HTML5, CSS3, JavaScript (Vanilla JS using Fetch API and EventSource).

## 4. Prerequisites

Before you start, make sure you have the following installed:

*   **Python 3.x**
*   **MongoDB Server (version 4.0+)**
    *   Ensure `mongod` and `mongosh` (or `mongo`) are accessible from your command line (added to PATH).

## 5. Configuration and Launch

### Important Note: MongoDB Replica Set

**Multi-document transactions** and **Change Streams** (key features of this project) **require** your MongoDB instance to be running as a **replica set**, not a standalone instance. The instructions below detail how to configure this.

### Project File Preparation

1.  **Directory Structure:** Ensure your project has the following structure:
    ```
    Nierelacyjne/
    ├── backend/
    │   ├── templates/
    │   │   └── index.html
    │   ├── app.py
    │   ├── db.py
    │   ├── requirements.txt
    │   └── seed.py
    └── static/
        └── style.css
    ```
2.  **`db.py` Configuration:**
    Open `backend/db.py` and ensure the `MONGO_URI` includes the `replicaSet` parameter:
    ```python
    # backend/db.py
    from pymongo import MongoClient
    import os

    # ENSURE THIS LINE INCLUDES "?replicaSet=rs0"
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
    DB_NAME = "interstellar_logistics"

    _client = None
    _db = None

    def get_db():
        global _client, _db
        if _db is None:
            _client = MongoClient(MONGO_URI)
            _db = _client[DB_NAME]
        return _db
    ```
3.  **`app.py` Configuration:**
    Open `backend/app.py` and ensure `Timestamp` is imported and the `to_json` function handles it:
    ```python
    # backend/app.py
    from flask import Flask, request, jsonify, send_from_directory, Response
    from flask_cors import CORS
    from bson import ObjectId, Timestamp # <-- ENSURE Timestamp IS IMPORTED HERE
    from datetime import datetime, timedelta
    import os, json

    from db import get_db

    app = Flask(__name__, static_folder='../static', static_url_path='/static')
    CORS(app)

    # ... (rest of app.py)

    # Helper: ObjectId/datetime conversion to JSON
    def to_json(doc):
        # ... (existing code)
        if isinstance(doc, Timestamp): # <-- ENSURE THIS LINE IS PRESENT
            return f"Timestamp(t={doc.time}, i={doc.inc})"
        return doc
    # ... (rest of app.py)
    ```
4.  **Install Python Dependencies:**
    ```bash
    # Navigate to the backend/ directory
    cd Nierelacyjne/backend/

    # Create and activate a virtual environment (recommended)
    python3 -m venv .venv
    source .venv/bin/activate  # macOS
    # .venv\Scripts\activate    # Windows PowerShell

    # Install dependencies
    pip install -r requirements.txt
    ```

### Starting MongoDB Replica Set (First Time or After Shutdown)

**You will need three separate terminal windows.**

**Terminal 1 (Control):**
1.  **Terminate ALL running `mongod` processes:**
    *   **macOS:** `ps aux | grep mongod` (find PIDs and `kill <PID>`). If using Homebrew: `brew services stop mongodb-community`.
    *   **Windows:** `tasklist | findstr mongod` (find PIDs and `taskkill /PID <PID> /F`).
2.  **Clean and prepare the MongoDB data directory:**
    *   **macOS:**
        ```bash
        rm -rf ~/mongodb_data/rs0-0  # WARNING: This will DELETE ALL data from this directory!
        mkdir -p ~/mongodb_data/rs0-0
        ```
    *   **Windows:**
        ```cmd
        rd /s /q C:\data\db\rs0-0  REM WARNING: This will DELETE ALL data from this directory!
        md C:\data\db\rs0-0
        ```

**Terminal 2 (Mongod - Must remain open!):**
1.  **Start `mongod` in replica set mode:**
    *   **macOS:**
        ```bash
        mongod --replSet rs0 --bind_ip localhost --port 27017 --dbpath ~/mongodb_data/rs0-0 --logpath ~/mongodb_data/rs0-0/mongodb.log
        ```
    *   **Windows:**
        ```cmd
        "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" --replSet rs0 --bind_ip localhost --port 27017 --dbpath C:\data\db\rs0-0 --logpath C:\data\db\rs0-0\mongodb.log
        ```
        *   **IMPORTANT:** Adjust the full path to `mongod.exe`!

**Terminal 3 (Mongosh):**
1.  **Initiate the replica set:**
    ```bash
    mongosh --port 27017
    # Once connected, in the mongosh shell (prompt test>):
    rs.initiate();
    # Wait a moment (up to 30 seconds) until the prompt changes to rs0:PRIMARY>.
    # Then you can type 'exit'.
    ```

### Seeding Data

If you deleted the MongoDB data directory or are running the project for the first time (after successfully configuring the replica set):

1.  In the terminal where you have your virtual environment active and are in the `backend/` directory:
    ```bash
    python seed.py
    ```

### Launching the Flask Application

1.  Ensure the MongoDB server is running as a replica set (Terminal 2 is open).
2.  In the terminal where you have your virtual environment active and are in the `backend/` directory:
    ```bash
    python app.py
    ```
3.  You should see a message like `Running on http://0.0.0.0:3000`.

## 6. Using the Application

1.  Open your web browser.
2.  Navigate to: `http://localhost:3000`
3.  The user interface will allow you to interact with all backend functionalities:
    *   View the list of ships.
    *   Retrieve ship and crew details.
    *   Update ship status (observe the "Aktualizacje w Czasie Rzeczywistym" section!).
    *   Add/remove cargo.
    *   Assign/unassign crew.
    *   Create new ships/crew members.
    *   Run analytical reports.
    *   **Test transactions:** Transfer a crew member between ships and observe the atomic operation.
    *   **Monitor Change Stream:** Observe the "Aktualizacje w Czasie Rzeczywistym" section - any changes in the `ships` collection (both from the UI and, for example, from the `mongosh` console) will appear there instantly.

## 7. Troubleshooting

*   **"Błąd połączenia z Change Stream. Upewnij się, że MongoDB działa jako replikaset."** (Error connecting to Change Stream. Ensure MongoDB is running as a replica set.)
    *   This usually means the `mongod` server is not running with the `--replSet rs0` option or was not initiated using `rs.initiate()`. Go through the [Starting MongoDB Replica Set](#starting-mongodb-replica-set-first-time-or-after-shutdown) section from the beginning.
*   **"Object of type Timestamp is not JSON serializable"**
    *   This means the `to_json` function in `app.py` has not been updated to handle the `bson.Timestamp` type. Check point 5 in the [Project File Preparation](#project-file-preparation) section.
*   **No data in dropdowns (crew, ships, routes):**
    *   Ensure `python seed.py` was run when MongoDB was operating as a replica set.
    *   Check your browser's developer console (F12) for JavaScript errors.
*   **Flask application fails to start (errors in the `python app.py` terminal):**
    *   Verify that the MongoDB server on port 27017 is definitely running (Terminal 2).
    *   Ensure all Python dependencies are installed (`pip install -r requirements.txt`).
    *   Check for syntax errors in `app.py` or `db.py`.

---