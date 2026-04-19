"""
Uruchom raz przed startem serwera: python seed.py
Tworzy kolekcje z przykładowymi danymi.
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime, timedelta
import random, os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["interstellar_logistics"]

# Wyczyść stare dane
for col in ["ships", "crew", "telemetry", "routes"]:
    db[col].drop()

print("[SEED] Kolekcje wyczyszczone")

# ─── ROUTES ───────────────────────────────────────────────────
route_ids = {
    "earth_mars":    ObjectId(),
    "mars_europa":   ObjectId(),
    "earth_luna":    ObjectId(),
    "mars_jupiter":  ObjectId(),
}

db["routes"].insert_many([
    {
        "_id": route_ids["earth_mars"],
        "name": "Earth → Mars",
        "origin": "Earth Orbit Station Alpha",
        "destination": "Mars Olympus Base",
        "distance_km": 225_000_000,
        "avg_duration_days": 210,
        "hazard_level": "moderate",
    },
    {
        "_id": route_ids["mars_europa"],
        "name": "Mars → Europa",
        "origin": "Mars Olympus Base",
        "destination": "Europa Research Outpost",
        "distance_km": 628_000_000,
        "avg_duration_days": 390,
        "hazard_level": "high",
    },
    {
        "_id": route_ids["earth_luna"],
        "name": "Earth → Luna",
        "origin": "Earth Orbit Station Alpha",
        "destination": "Luna Colony Artemis",
        "distance_km": 384_000,
        "avg_duration_days": 4,
        "hazard_level": "low",
    },
    {
        "_id": route_ids["mars_jupiter"],
        "name": "Mars → Jupiter",
        "origin": "Mars Olympus Base",
        "destination": "Jupiter Station Juno",
        "distance_km": 550_000_000,
        "avg_duration_days": 330,
        "hazard_level": "extreme",
    },
])
print("[SEED] Routes OK")

# ─── CREW ─────────────────────────────────────────────────────
# Załoga istnieje NIEZALEŻNIE od statku → osobna kolekcja
# Statek przechowuje tylko listę ObjectId
crew_ids = {k: ObjectId() for k in [
    "kapitan", "lekarz", "inzynier", "pilot",
    "naukowiec", "mechanik", "pilot2", "lekarz2",
    "inzynier2", "dowodca"
]}

db["crew"].insert_many([
    {
        "_id": crew_ids["kapitan"],
        "name": "Aleksandra Nowak",
        "role": "Captain",
        "rank": "Commander",
        "certifications": ["Deep Space Navigation", "Emergency Command", "EVA"],
        "medical": {"blood_type": "A+", "last_checkup": datetime(2025, 11, 1), "fit_for_duty": True},
        "experience_years": 14,
    },
    {
        "_id": crew_ids["lekarz"],
        "name": "Dr. James Chen",
        "role": "Chief Medical Officer",
        "rank": "Lieutenant Commander",
        "certifications": ["Space Medicine", "Surgery", "Psychology"],
        "medical": {"blood_type": "O-", "last_checkup": datetime(2025, 12, 10), "fit_for_duty": True},
        "experience_years": 9,
    },
    {
        "_id": crew_ids["inzynier"],
        "name": "Piotr Wiśniewski",
        "role": "Chief Engineer",
        "rank": "Lieutenant",
        "certifications": ["Reactor Systems", "Life Support", "Propulsion"],
        "medical": {"blood_type": "B+", "last_checkup": datetime(2025, 10, 22), "fit_for_duty": True},
        "experience_years": 11,
    },
    {
        "_id": crew_ids["pilot"],
        "name": "Yuki Tanaka",
        "role": "Pilot",
        "rank": "Lieutenant",
        "certifications": ["Deep Space Navigation", "Emergency Landing", "EVA"],
        "medical": {"blood_type": "AB+", "last_checkup": datetime(2025, 11, 30), "fit_for_duty": True},
        "experience_years": 7,
    },
    {
        "_id": crew_ids["naukowiec"],
        "name": "Dr. Sofia Reyes",
        "role": "Science Officer",
        "rank": "Ensign",
        "certifications": ["Xenobiology", "Geology", "Atmospheric Analysis"],
        "medical": {"blood_type": "A-", "last_checkup": datetime(2025, 9, 15), "fit_for_duty": True},
        "experience_years": 5,
    },
    {
        "_id": crew_ids["mechanik"],
        "name": "Boris Volkov",
        "role": "Mechanic",
        "rank": "Petty Officer",
        "certifications": ["Hull Repair", "Robotics", "Welding"],
        "medical": {"blood_type": "O+", "last_checkup": datetime(2025, 8, 1), "fit_for_duty": False},
        "experience_years": 6,
    },
    {
        "_id": crew_ids["pilot2"],
        "name": "Amara Okafor",
        "role": "Pilot",
        "rank": "Lieutenant",
        "certifications": ["Deep Space Navigation", "Combat Maneuvers", "EVA"],
        "medical": {"blood_type": "B-", "last_checkup": datetime(2026, 1, 5), "fit_for_duty": True},
        "experience_years": 8,
    },
    {
        "_id": crew_ids["lekarz2"],
        "name": "Dr. Ivan Petrov",
        "role": "Medical Officer",
        "rank": "Ensign",
        "certifications": ["Space Medicine", "Trauma Care"],
        "medical": {"blood_type": "A+", "last_checkup": datetime(2026, 1, 20), "fit_for_duty": True},
        "experience_years": 3,
    },
    {
        "_id": crew_ids["inzynier2"],
        "name": "Mei Lin",
        "role": "Systems Engineer",
        "rank": "Lieutenant",
        "certifications": ["Life Support", "Navigation Systems", "AI Maintenance"],
        "medical": {"blood_type": "O+", "last_checkup": datetime(2025, 12, 1), "fit_for_duty": True},
        "experience_years": 9,
    },
    {
        "_id": crew_ids["dowodca"],
        "name": "Colonel Marcus Webb",
        "role": "Captain",
        "rank": "Colonel",
        "certifications": ["Deep Space Navigation", "Emergency Command", "Combat Tactics", "EVA"],
        "medical": {"blood_type": "AB-", "last_checkup": datetime(2026, 2, 1), "fit_for_duty": True},
        "experience_years": 20,
    },
])
print("[SEED] Crew OK")

# ─── SHIPS ────────────────────────────────────────────────────
# Cargo EMBEDDED w dokumencie statku — ładunek należy do rejsu,
# nie istnieje samodzielnie poza nim.
# Załoga jako lista ObjectId (referencja, bo istnieje niezależnie).
ship_ids = {k: ObjectId() for k in ["ares", "hermes", "artemis", "prometheus"]}

db["ships"].insert_many([
    {
        "_id": ship_ids["ares"],
        "name": "IMSV Ares",
        "registry": "IM-2089-A",
        "class": "Heavy Freighter",
        "status": "in_transit",
        "route_id": route_ids["earth_mars"],
        "departure_date": datetime(2026, 2, 14),
        "eta": datetime(2026, 9, 12),
        "current_position": {"x_au": 0.82, "y_au": 0.41, "z_au": 0.02},
        "cargo": [
            {"item_id": "CRG-001", "type": "oxygen",      "description": "Liquid Oxygen Tanks",          "quantity_kg": 12000, "max_capacity_kg": 15000, "hazardous": False, "destination": "Mars Olympus Base"},
            {"item_id": "CRG-002", "type": "food",        "description": "Freeze-Dried Rations",         "quantity_kg": 2700,  "max_capacity_kg": 20000, "hazardous": False, "destination": "Mars Olympus Base"},
            {"item_id": "CRG-003", "type": "fuel",        "description": "Deuterium Fuel Cells",         "quantity_kg": 45000, "max_capacity_kg": 50000, "hazardous": True,  "destination": "Mars Olympus Base"},
            {"item_id": "CRG-004", "type": "spare_parts", "description": "Reactor Shielding Panels",     "quantity_kg": 8000,  "max_capacity_kg": 10000, "hazardous": False, "destination": "Mars Olympus Base"},
        ],
        "crew_ids": [crew_ids["kapitan"], crew_ids["lekarz"], crew_ids["inzynier"], crew_ids["pilot"]],
        "systems": {"reactor_output_percent": 78, "life_support_status": "nominal", "hull_integrity_percent": 97, "fuel_remaining_percent": 61},
    },
    {
        "_id": ship_ids["hermes"],
        "name": "IMSV Hermes",
        "registry": "IM-2091-H",
        "class": "Scout Vessel",
        "status": "in_transit",
        "route_id": route_ids["mars_europa"],
        "departure_date": datetime(2026, 1, 3),
        "eta": datetime(2027, 1, 28),
        "current_position": {"x_au": 3.21, "y_au": -1.05, "z_au": 0.15},
        "cargo": [
            {"item_id": "CRG-010", "type": "scientific_equipment", "description": "Ice Drill Assembly",       "quantity_kg": 3200, "max_capacity_kg": 5000, "hazardous": False, "destination": "Europa Research Outpost"},
            {"item_id": "CRG-011", "type": "food",                 "description": "Compressed Protein Packs", "quantity_kg": 800,  "max_capacity_kg": 8000, "hazardous": False, "destination": "Europa Research Outpost"},
            {"item_id": "CRG-012", "type": "oxygen",               "description": "Emergency O2 Canisters",   "quantity_kg": 500,  "max_capacity_kg": 4000, "hazardous": False, "destination": "Europa Research Outpost"},
        ],
        "crew_ids": [crew_ids["pilot2"], crew_ids["lekarz2"], crew_ids["naukowiec"]],
        "systems": {"reactor_output_percent": 55, "life_support_status": "nominal", "hull_integrity_percent": 91, "fuel_remaining_percent": 43},
    },
    {
        "_id": ship_ids["artemis"],
        "name": "IMSV Artemis",
        "registry": "IM-2085-AR",
        "class": "Passenger Freighter",
        "status": "docked",
        "route_id": route_ids["earth_luna"],
        "departure_date": datetime(2026, 4, 15),
        "eta": datetime(2026, 4, 19),
        "current_position": {"x_au": 0.0, "y_au": 0.0, "z_au": 0.0},
        "cargo": [
            {"item_id": "CRG-020", "type": "food",            "description": "Fresh Vegetables (hydroponic)",    "quantity_kg": 5000,  "max_capacity_kg": 8000,  "hazardous": False, "destination": "Luna Colony Artemis"},
            {"item_id": "CRG-021", "type": "medical_supplies","description": "Emergency Surgery Kit Type-IV",    "quantity_kg": 400,   "max_capacity_kg": 1000,  "hazardous": False, "destination": "Luna Colony Artemis"},
            {"item_id": "CRG-022", "type": "spare_parts",     "description": "Habitat Dome Segments",            "quantity_kg": 12000, "max_capacity_kg": 15000, "hazardous": False, "destination": "Luna Colony Artemis"},
        ],
        "crew_ids": [crew_ids["inzynier2"], crew_ids["mechanik"]],
        "systems": {"reactor_output_percent": 20, "life_support_status": "standby", "hull_integrity_percent": 100, "fuel_remaining_percent": 88},
    },
    {
        "_id": ship_ids["prometheus"],
        "name": "IMSV Prometheus",
        "registry": "IM-2078-P",
        "class": "Dreadnought Freighter",
        "status": "in_transit",
        "route_id": route_ids["mars_jupiter"],
        "departure_date": datetime(2025, 12, 1),
        "eta": datetime(2026, 11, 10),
        "current_position": {"x_au": 2.10, "y_au": 0.77, "z_au": -0.08},
        "cargo": [
            {"item_id": "CRG-030", "type": "fuel",        "description": "Antimatter Containment Pods",        "quantity_kg": 200,   "max_capacity_kg": 500,   "hazardous": True,  "destination": "Jupiter Station Juno"},
            {"item_id": "CRG-031", "type": "food",        "description": "Long-Term Ration Packs (2yr supply)","quantity_kg": 3000,  "max_capacity_kg": 20000, "hazardous": False, "destination": "Jupiter Station Juno"},
            {"item_id": "CRG-032", "type": "oxygen",      "description": "High-Pressure Oxygen Tanks",         "quantity_kg": 8000,  "max_capacity_kg": 18000, "hazardous": False, "destination": "Jupiter Station Juno"},
            {"item_id": "CRG-033", "type": "spare_parts", "description": "Station Reactor Core (replacement)", "quantity_kg": 25000, "max_capacity_kg": 30000, "hazardous": True,  "destination": "Jupiter Station Juno"},
        ],
        "crew_ids": [crew_ids["dowodca"], crew_ids["inzynier"], crew_ids["lekarz"], crew_ids["pilot"]],
        "systems": {"reactor_output_percent": 92, "life_support_status": "nominal", "hull_integrity_percent": 83, "fuel_remaining_percent": 29},
    },
])
print("[SEED] Ships OK")

# ─── TELEMETRY ────────────────────────────────────────────────
# Osobna kolekcja — dane nieograniczone (anti-pattern gdyby embedded).
# Indeks na (ship_id, timestamp) dla wydajnych zapytań.
now = datetime.utcnow()
telemetry_docs = []
for sid in ship_ids.values():
    for i in range(59, -1, -1):
        telemetry_docs.append({
            "ship_id": sid,
            "timestamp": now - timedelta(hours=i),
            "temperature_celsius": round(20 + random.uniform(-2.5, 2.5), 2),
            "pressure_kpa":        round(101 + random.uniform(-2, 2), 2),
            "radiation_msv":       round(0.1 + random.uniform(0, 0.5), 3),
            "reactor_temp_celsius":round(450 + random.uniform(-15, 15), 1),
            "fuel_consumption_kg_h": round(12 + random.uniform(0, 3), 2),
            "speed_km_s":          round(28 + random.uniform(0, 4), 2),
        })

db["telemetry"].insert_many(telemetry_docs)
db["telemetry"].create_index([("ship_id", ASCENDING), ("timestamp", DESCENDING)])

# Dodatkowe indeksy
db["ships"].create_index([("status", ASCENDING)])
db["ships"].create_index([("route_id", ASCENDING)])
db["crew"].create_index([("role", ASCENDING)])

print(f"[SEED] Telemetry OK ({len(telemetry_docs)} rekordów)")
print("[SEED] ✅ Gotowe! Uruchom: python app.py")
client.close()