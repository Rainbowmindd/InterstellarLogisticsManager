"""
INTERSTELLAR LOGISTICS MANAGER — Flask Backend
Surowe zapytania PyMongo, zero ORM.

Uruchomienie:
    pip install -r requirements.txt
    python seed.py
    python app.py
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime, timedelta
import os, json

from db import get_db

app = Flask(__name__, static_folder="../templates", static_url_path="")
CORS(app)

# ── Pomocnik: konwersja ObjectId/datetime → JSON ──────────────
def to_json(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [to_json(d) for d in doc]
    if isinstance(doc, dict):
        return {k: to_json(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


# ═══════════════════════════════════════════════════════════════
# SHIPS
# ═══════════════════════════════════════════════════════════════

@app.route("/api/ships", methods=["GET"])
def list_ships():
    """
    Lista statków z dołączoną nazwą trasy i liczbą załogi.
    Używa $lookup (odpowiednik JOIN) oraz $project.
    """
    db = get_db()

    pipeline = [
        # JOIN z kolekcją routes
        {
            "$lookup": {
                "from": "routes",
                "localField": "route_id",
                "foreignField": "_id",
                "as": "route",
            }
        },
        {"$unwind": {"path": "$route", "preserveNullAndEmptyArrays": True}},
        # Zwróć tylko potrzebne pola
        {
            "$project": {
                "name": 1,
                "registry": 1,
                "class": 1,
                "status": 1,
                "departure_date": 1,
                "eta": 1,
                "route.name": 1,
                "route.hazard_level": 1,
                "systems.hull_integrity_percent": 1,
                "systems.fuel_remaining_percent": 1,
                "systems.life_support_status": 1,
                "crew_count": {"$size": "$crew_ids"},
                "cargo_count": {"$size": "$cargo"},
            }
        },
        {"$sort": {"name": 1}},
    ]

    ships = list(db["ships"].aggregate(pipeline))
    return jsonify(to_json(ships))


@app.route("/api/ships/<ship_id>", methods=["GET"])
def get_ship(ship_id):
    """
    Pełny dokument statku: embedded cargo + JOIN route + populate crew.
    Kluczowa zaleta MongoDB: cargo jest już w dokumencie — zero dodatkowych
    zapytań. W SQL wymagałoby to JOIN-ów przez 5+ tabel.
    """
    db = get_db()

    pipeline = [
        {"$match": {"_id": ObjectId(ship_id)}},
        # Dołącz trasę
        {
            "$lookup": {
                "from": "routes",
                "localField": "route_id",
                "foreignField": "_id",
                "as": "route",
            }
        },
        {"$unwind": {"path": "$route", "preserveNullAndEmptyArrays": True}},
        # Rozwiń crew_ids → pełne dokumenty członków załogi
        {
            "$lookup": {
                "from": "crew",
                "localField": "crew_ids",
                "foreignField": "_id",
                "as": "crew",
            }
        },
    ]

    result = list(db["ships"].aggregate(pipeline))
    if not result:
        return jsonify({"error": "Statek nie znaleziony"}), 404
    return jsonify(to_json(result[0]))


@app.route("/api/ships", methods=["POST"])
def create_ship():
    """Dodaj nowy statek."""
    db = get_db()
    data = request.get_json()

    doc = {
        "name":           data["name"],
        "registry":       data["registry"],
        "class":          data.get("class", "Heavy Freighter"),
        "status":         "docked",
        "route_id":       ObjectId(data["route_id"]) if data.get("route_id") else None,
        "departure_date": datetime.fromisoformat(data["departure_date"]) if data.get("departure_date") else None,
        "eta":            datetime.fromisoformat(data["eta"]) if data.get("eta") else None,
        "current_position": {"x_au": 0.0, "y_au": 0.0, "z_au": 0.0},
        "cargo": [],
        "crew_ids": [],
        "systems": {
            "reactor_output_percent":  0,
            "life_support_status":     "standby",
            "hull_integrity_percent":  100,
            "fuel_remaining_percent":  100,
        },
    }

    result = db["ships"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify(to_json(doc)), 201


@app.route("/api/ships/<ship_id>/status", methods=["PATCH"])
def update_ship_status(ship_id):
    """Zmień status statku."""
    db = get_db()
    data = request.get_json()
    status = data.get("status")

    valid = {"docked", "in_transit", "emergency", "decommissioned"}
    if status not in valid:
        return jsonify({"error": f"Nieprawidłowy status. Dozwolone: {valid}"}), 400

    # Surowe zapytanie $set — bez ORM
    db["ships"].update_one(
        {"_id": ObjectId(ship_id)},
        {"$set": {"status": status}}
    )
    return jsonify({"success": True, "status": status})


@app.route("/api/ships/<ship_id>/systems", methods=["PATCH"])
def update_ship_systems(ship_id):
    """Aktualizuj parametry systemów pokładowych."""
    db = get_db()
    data = request.get_json()

    update = {}
    if "reactor_output_percent"  in data: update["systems.reactor_output_percent"]  = data["reactor_output_percent"]
    if "life_support_status"     in data: update["systems.life_support_status"]     = data["life_support_status"]
    if "hull_integrity_percent"  in data: update["systems.hull_integrity_percent"]  = data["hull_integrity_percent"]
    if "fuel_remaining_percent"  in data: update["systems.fuel_remaining_percent"]  = data["fuel_remaining_percent"]

    db["ships"].update_one({"_id": ObjectId(ship_id)}, {"$set": update})
    return jsonify({"success": True})


# ── Cargo (embedded array operations) ─────────────────────────

@app.route("/api/ships/<ship_id>/cargo", methods=["POST"])
def add_cargo(ship_id):
    """
    Dodaj pozycję ładunku do embedded array w dokumencie statku.
    $push — bezpośrednia operacja na tablicy bez pobierania dokumentu.
    """
    db = get_db()
    data = request.get_json()

    item = {
        "item_id":         f"CRG-{int(datetime.utcnow().timestamp())}",
        "type":            data["type"],
        "description":     data["description"],
        "quantity_kg":     int(data["quantity_kg"]),
        "max_capacity_kg": int(data["max_capacity_kg"]),
        "hazardous":       bool(data.get("hazardous", False)),
        "destination":     data.get("destination", ""),
    }

    db["ships"].update_one(
        {"_id": ObjectId(ship_id)},
        {"$push": {"cargo": item}}   # $push bezpośrednio na embedded array
    )
    return jsonify(to_json(item)), 201


@app.route("/api/ships/<ship_id>/cargo/<item_id>", methods=["DELETE"])
def remove_cargo(ship_id, item_id):
    """
    Usuń pozycję z embedded array.
    $pull — usuwa elementy spełniające warunek bez pobierania dokumentu.
    """
    db = get_db()
    db["ships"].update_one(
        {"_id": ObjectId(ship_id)},
        {"$pull": {"cargo": {"item_id": item_id}}}   # $pull z warunkowym dopasowaniem
    )
    return jsonify({"success": True})


# ── Crew assignment ────────────────────────────────────────────

@app.route("/api/ships/<ship_id>/crew", methods=["POST"])
def assign_crew(ship_id):
    """
    Przydziel załoganta do statku.
    $addToSet — dodaje ObjectId do tablicy tylko jeśli jeszcze go nie ma.
    """
    db = get_db()
    crew_id = ObjectId(request.get_json()["crew_id"])

    db["ships"].update_one(
        {"_id": ObjectId(ship_id)},
        {"$addToSet": {"crew_ids": crew_id}}   # $addToSet = brak duplikatów
    )
    return jsonify({"success": True})


@app.route("/api/ships/<ship_id>/crew/<crew_id>", methods=["DELETE"])
def remove_crew_from_ship(ship_id, crew_id):
    """Odwołaj załoganta ze statku ($pull z tablicy crew_ids)."""
    db = get_db()
    db["ships"].update_one(
        {"_id": ObjectId(ship_id)},
        {"$pull": {"crew_ids": ObjectId(crew_id)}}
    )
    return jsonify({"success": True})


# ═══════════════════════════════════════════════════════════════
# CREW
# ═══════════════════════════════════════════════════════════════

@app.route("/api/crew", methods=["GET"])
def list_crew():
    """Lista załogi. Opcjonalny filtr ?role=Pilot"""
    db = get_db()
    query = {}
    if request.args.get("role"):
        query["role"] = request.args["role"]   # surowe find() z filtrem

    crew = list(db["crew"].find(query).sort("name", 1))
    return jsonify(to_json(crew))


@app.route("/api/crew/<crew_id>", methods=["GET"])
def get_crew_member(crew_id):
    """
    Szczegóły załoganta + lista statków, do których jest przydzielony.
    Odwrotna strona relacji: szukamy statków zawierających ten crew_id.
    """
    db = get_db()
    member = db["crew"].find_one({"_id": ObjectId(crew_id)})
    if not member:
        return jsonify({"error": "Nie znaleziono"}), 404

    # Znajdź statki zawierające ten ObjectId w tablicy crew_ids
    assignments = list(
        db["ships"].find(
            {"crew_ids": ObjectId(crew_id)},
            {"name": 1, "registry": 1, "status": 1}   # projekcja — tylko potrzebne pola
        )
    )

    member["assignments"] = assignments
    return jsonify(to_json(member))


@app.route("/api/crew", methods=["POST"])
def create_crew_member():
    """Dodaj nowego członka załogi."""
    db = get_db()
    data = request.get_json()

    doc = {
        "name":             data["name"],
        "role":             data["role"],
        "rank":             data.get("rank", "Ensign"),
        "certifications":   data.get("certifications", []),
        "medical": {
            "blood_type":    data.get("medical", {}).get("blood_type", "Unknown"),
            "last_checkup":  datetime.utcnow(),
            "fit_for_duty":  data.get("medical", {}).get("fit_for_duty", True),
        },
        "experience_years": int(data.get("experience_years", 0)),
    }

    result = db["crew"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify(to_json(doc)), 201


@app.route("/api/crew/<crew_id>/medical", methods=["PATCH"])
def update_medical(crew_id):
    """Aktualizuj status medyczny."""
    db = get_db()
    data = request.get_json()

    update = {}
    if "fit_for_duty" in data:
        update["medical.fit_for_duty"] = bool(data["fit_for_duty"])
    if "last_checkup" in data:
        update["medical.last_checkup"] = datetime.fromisoformat(data["last_checkup"])
    else:
        update["medical.last_checkup"] = datetime.utcnow()

    db["crew"].update_one({"_id": ObjectId(crew_id)}, {"$set": update})
    return jsonify({"success": True})


# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/api/routes", methods=["GET"])
def list_routes():
    db = get_db()
    routes = list(db["routes"].find({}).sort("name", 1))
    return jsonify(to_json(routes))


# ═══════════════════════════════════════════════════════════════
# TELEMETRY
# ═══════════════════════════════════════════════════════════════

@app.route("/api/telemetry/<ship_id>", methods=["GET"])
def get_telemetry(ship_id):
    """
    Ostatnie N odczytów telemetrii dla statku.
    Wydajne dzięki indeksowi złożonemu (ship_id, timestamp).
    """
    db = get_db()
    limit = int(request.args.get("limit", 24))

    readings = list(
        db["telemetry"]
        .find({"ship_id": ObjectId(ship_id)})    # filtr po ship_id
        .sort("timestamp", -1)                    # najnowsze pierwsze
        .limit(limit)
    )
    readings.reverse()   # chronologicznie dla wykresu
    return jsonify(to_json(readings))


@app.route("/api/telemetry/<ship_id>", methods=["POST"])
def add_telemetry(ship_id):
    """Dodaj nowy odczyt telemetrii."""
    db = get_db()
    data = request.get_json()
    doc = {"ship_id": ObjectId(ship_id), "timestamp": datetime.utcnow(), **data}
    result = db["telemetry"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify(to_json(doc)), 201


# ═══════════════════════════════════════════════════════════════
# ANALYTICS — Aggregation Pipeline
# ═══════════════════════════════════════════════════════════════

@app.route("/api/analytics/fleet-summary", methods=["GET"])
def fleet_summary():
    """
    Statystyki całej floty — jeden $group po wszystkich statkach.
    """
    db = get_db()

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_ships": {"$sum": 1},
                "in_transit":  {"$sum": {"$cond": [{"$eq": ["$status", "in_transit"]}, 1, 0]}},
                "docked":      {"$sum": {"$cond": [{"$eq": ["$status", "docked"]},     1, 0]}},
                "emergency":   {"$sum": {"$cond": [{"$eq": ["$status", "emergency"]},  1, 0]}},
                "avg_hull":    {"$avg": "$systems.hull_integrity_percent"},
                "avg_fuel":    {"$avg": "$systems.fuel_remaining_percent"},
                "total_cargo_types": {"$sum": {"$size": "$cargo"}},
            }
        }
    ]

    result = list(db["ships"].aggregate(pipeline))
    return jsonify(to_json(result[0] if result else {}))


@app.route("/api/analytics/critical-missions", methods=["GET"])
def critical_missions():
    """
    Statki IN TRANSIT gdzie:
      - w załodze jest lekarz (CMO lub Medical Officer)
      - zapasy żywności < 20% pojemności

    Pokazuje złożony pipeline:
      $lookup (crew) → $lookup (route) → $addFields ($filter na embedded array)
      → $addFields (obliczenie food_percent) → $match (oba warunki naraz)
    """
    db = get_db()

    pipeline = [
        # Tylko statki w locie
        {"$match": {"status": "in_transit"}},

        # JOIN: rozwiń crew_ids → pełne dokumenty załogi
        {
            "$lookup": {
                "from": "crew",
                "localField": "crew_ids",
                "foreignField": "_id",
                "as": "crew",
            }
        },

        # JOIN: dołącz informacje o trasie
        {
            "$lookup": {
                "from": "routes",
                "localField": "route_id",
                "foreignField": "_id",
                "as": "route",
            }
        },
        {"$unwind": {"path": "$route", "preserveNullAndEmptyArrays": True}},

        # Oblicz pola pomocnicze:
        {
            "$addFields": {
                # Filtruj embedded array cargo — tylko pozycje typu 'food'
                "food_cargo": {
                    "$filter": {
                        "input": "$cargo",
                        "as": "item",
                        "cond": {"$eq": ["$$item.type", "food"]},
                    }
                },
                # Sprawdź czy w tablicy crew jest lekarz
                "has_doctor": {
                    "$gt": [
                        {
                            "$size": {
                                "$filter": {
                                    "input": "$crew",
                                    "as": "c",
                                    "cond": {
                                        "$in": ["$$c.role", ["Chief Medical Officer", "Medical Officer"]]
                                    },
                                }
                            }
                        },
                        0,
                    ]
                },
            }
        },
        # Oblicz sumy żywności
        {
            "$addFields": {
                "food_qty":      {"$sum": "$food_cargo.quantity_kg"},
                "food_capacity": {"$sum": "$food_cargo.max_capacity_kg"},
            }
        },
        # Oblicz procent
        {
            "$addFields": {
                "food_percent": {
                    "$cond": [
                        {"$gt": ["$food_capacity", 0]},
                        {"$multiply": [{"$divide": ["$food_qty", "$food_capacity"]}, 100]},
                        100,
                    ]
                }
            }
        },

        # Filtruj: lekarz AND żywność < 20%
        {
            "$match": {
                "has_doctor":   True,
                "food_percent": {"$lt": 20},
            }
        },

        {
            "$project": {
                "name": 1, "registry": 1,
                "route.name": 1, "route.hazard_level": 1,
                "eta": 1, "has_doctor": 1,
                "food_percent": {"$round": ["$food_percent", 1]},
                "crew_count": {"$size": "$crew"},
                "systems.fuel_remaining_percent": 1,
            }
        },
    ]

    results = list(db["ships"].aggregate(pipeline))
    return jsonify(to_json(results))


@app.route("/api/analytics/cargo-breakdown", methods=["GET"])
def cargo_breakdown():
    """
    Łączna masa ładunku wg typu w całej flocie.
    $unwind rozkłada embedded array cargo na osobne dokumenty,
    $group zlicza sumy.
    """
    db = get_db()

    pipeline = [
        # Rozwiń embedded array cargo — każda pozycja staje się osobnym dokumentem
        {"$unwind": "$cargo"},
        {
            "$group": {
                "_id":              "$cargo.type",
                "total_kg":         {"$sum": "$cargo.quantity_kg"},
                "item_count":       {"$sum": 1},
                "hazardous_count":  {"$sum": {"$cond": ["$cargo.hazardous", 1, 0]}},
            }
        },
        {"$sort": {"total_kg": -1}},
    ]

    results = list(db["ships"].aggregate(pipeline))
    return jsonify(to_json(results))


@app.route("/api/analytics/telemetry-avg/<ship_id>", methods=["GET"])
def telemetry_avg(ship_id):
    """Średnie parametry telemetrii za ostatnie N godzin."""
    db = get_db()
    hours = int(request.args.get("hours", 24))
    since = datetime.utcnow() - timedelta(hours=hours)

    pipeline = [
        {
            "$match": {
                "ship_id":  ObjectId(ship_id),
                "timestamp": {"$gte": since},   # zakres czasowy
            }
        },
        {
            "$group": {
                "_id":                   None,
                "avg_temp":              {"$avg": "$temperature_celsius"},
                "avg_radiation":         {"$avg": "$radiation_msv"},
                "avg_fuel_consumption":  {"$avg": "$fuel_consumption_kg_h"},
                "avg_speed":             {"$avg": "$speed_km_s"},
                "readings":              {"$sum": 1},
            }
        },
    ]

    result = list(db["ships"].aggregate(pipeline))
    return jsonify(to_json(result[0] if result else {}))

from flask import render_template

@app.route("/")
@app.route("/<path:path>")
def serve_frontend(path=""):
    return render_template("index.html")


if __name__ == "__main__":
    print("\n🚀 Interstellar Logistics Manager — Flask Backend")
    print("   http://localhost:3000")
    print("   Pierwsze uruchomienie? Najpierw: python seed.py\n")
    app.run(host="0.0.0.0", port=3000, debug=True)