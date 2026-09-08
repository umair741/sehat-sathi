"""Seed sample facilities and doctors for Sehat Sathi (rural/semi-urban Pakistan).

Usage:
    $env:SUPABASE_URL="https://..."
    $env:SUPABASE_KEY="sb_secret_..."
    venv\Scripts\python.exe scripts\seed_facilities.py
"""

import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("Error: set SUPABASE_URL and SUPABASE_KEY env vars.")
        print("Use the service_role key so RLS does not block inserts.")
        sys.exit(1)

    db = create_client(url, key)

    # Clear old demo data before re-seeding
    try:
        db.table("bookings").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("doctors").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("facilities").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    except Exception as e:
        print("Cleanup warning (can ignore on first run):", e)

    facilities = [
        {
            "name": "BHU Sukkur",
            "type": "BHU",
            "district": "Sukkur",
            "tehsil": "Sukkur City",
            "address": "Military Road, Sukkur, Sindh",
            "phone": "071-9310123",
            "lat": 27.7135,
            "lng": 68.8487,
        },
        {
            "name": "RHC Rohri",
            "type": "RHC",
            "district": "Sukkur",
            "tehsil": "Rohri",
            "address": "Lansdowne Bridge Road, Rohri",
            "phone": "071-9320456",
            "lat": 27.6833,
            "lng": 68.8888,
        },
        {
            "name": "Al-Madina Clinic",
            "type": "Clinic",
            "district": "Sukkur",
            "tehsil": "Pano Aqil",
            "address": "Main Bazaar, Pano Aqil",
            "phone": "071-9331122",
            "lat": 27.5833,
            "lng": 69.1167,
        },
        {
            "name": "Civil Hospital Sukkur",
            "type": "Hospital",
            "district": "Sukkur",
            "tehsil": "Sukkur City",
            "address": "Minara Road, Sukkur",
            "phone": "071-9309033",
            "lat": 27.7050,
            "lng": 68.8570,
        },
        {
            "name": "BHU Khairpur",
            "type": "BHU",
            "district": "Khairpur",
            "tehsil": "Khairpur",
            "address": "Station Road, Khairpur",
            "phone": "071-9340123",
            "lat": 27.5333,
            "lng": 68.7667,
        },
    ]

    created = []
    for f in facilities:
        res = db.table("facilities").insert(f).execute()
        if res.data:
            created.append(res.data[0])
        else:
            print(f"Failed to insert facility: {f['name']}")

    if not created:
        print("No facilities were inserted.")
        sys.exit(1)

    doctors = [
        {"facility_id": created[0]["id"], "name": "Dr. Ayesha Khan", "specialty": "General Physician", "qualification": "MBBS"},
        {"facility_id": created[0]["id"], "name": "Dr. Bilal Ahmed", "specialty": "Child Specialist", "qualification": "MCPS"},
        {"facility_id": created[1]["id"], "name": "Dr. Farooq Siddiqui", "specialty": "General Physician", "qualification": "MBBS"},
        {"facility_id": created[2]["id"], "name": "Dr. Sana Malik", "specialty": "Gynecologist", "qualification": "FCPS"},
        {"facility_id": created[2]["id"], "name": "Dr. Usman Tariq", "specialty": "General Physician", "qualification": "MBBS"},
        {"facility_id": created[3]["id"], "name": "Dr. Nadia Hussain", "specialty": "Emergency Medicine", "qualification": "FCPS"},
        {"facility_id": created[4]["id"], "name": "Dr. Imran Raza", "specialty": "General Physician", "qualification": "MBBS"},
    ]

    for d in doctors:
        db.table("doctors").insert(d).execute()

    print(f"Seeded {len(created)} facilities and {len(doctors)} doctors.")


if __name__ == "__main__":
    main()

