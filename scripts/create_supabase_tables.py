"""Create Sehat Sathi tables directly in Supabase PostgreSQL.

Usage:
1. Go to Supabase dashboard → Settings → Database
2. Copy the Connection String (looks like postgresql://postgres:PASSWORD@db.xxxx.supabase.co:5432/postgres)
3. Set it as env var:
       $env:DATABASE_URL="postgresql://postgres:PASSWORD@db.zmdcvaarifpvtunvuncc.supabase.co:5432/postgres"
4. Run: python scripts/create_supabase_tables.py
"""

import os
import sys
import psycopg2


def get_connection_string() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL env var not set.")
        print("Copy the connection string from Supabase Settings -> Database")
        sys.exit(1)
    return db_url


SCHEMA_SQL = """
-- conversations table
CREATE TABLE IF NOT EXISTS conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- messages table
CREATE TABLE IF NOT EXISTS messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  route TEXT,
  severity TEXT,
  timestamp TIMESTAMPTZ DEFAULT now()
);

-- profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  role TEXT DEFAULT 'patient',
  full_name TEXT,
  phone TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- facilities table (BHU / RHC / Clinic / Hospital)
CREATE TABLE IF NOT EXISTS facilities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  district TEXT NOT NULL,
  tehsil TEXT,
  address TEXT,
  phone TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- doctors table (linked to a facility)
CREATE TABLE IF NOT EXISTS doctors (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  facility_id UUID REFERENCES facilities(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  specialty TEXT,
  qualification TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- bookings table (appointment requests / tokens)
CREATE TABLE IF NOT EXISTS bookings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES auth.users(id) NOT NULL,
  doctor_id UUID REFERENCES doctors(id) NOT NULL,
  facility_id UUID REFERENCES facilities(id) NOT NULL,
  requested_date DATE NOT NULL,
  slot TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  token TEXT UNIQUE NOT NULL,
  patient_phone TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Prevent double-booking: same doctor cannot have two confirmed bookings on same date+slot
CREATE UNIQUE INDEX IF NOT EXISTS unique_confirmed_slot
  ON bookings (doctor_id, requested_date, slot)
  WHERE status = 'confirmed';

-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE facilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

-- RLS policies
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'conversations' AND policyname = 'Users can see own conversations'
  ) THEN
    CREATE POLICY "Users can see own conversations" ON conversations
      FOR SELECT USING (user_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'conversations' AND policyname = 'Users can create own conversations'
  ) THEN
    CREATE POLICY "Users can create own conversations" ON conversations
      FOR INSERT WITH CHECK (user_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'messages' AND policyname = 'Users can see own messages'
  ) THEN
    CREATE POLICY "Users can see own messages" ON messages
      FOR SELECT USING (user_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'messages' AND policyname = 'Users can create own messages'
  ) THEN
    CREATE POLICY "Users can create own messages" ON messages
      FOR INSERT WITH CHECK (user_id = auth.uid());
  END IF;

  -- profiles policies
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'profiles' AND policyname = 'Users can see own profile'
  ) THEN
    CREATE POLICY "Users can see own profile" ON profiles
      FOR SELECT USING (id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'profiles' AND policyname = 'Users can update own profile'
  ) THEN
    CREATE POLICY "Users can update own profile" ON profiles
      FOR UPDATE USING (id = auth.uid());
  END IF;

  -- facilities / doctors are public read
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'facilities' AND policyname = 'Public can view facilities'
  ) THEN
    CREATE POLICY "Public can view facilities" ON facilities
      FOR SELECT USING (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'doctors' AND policyname = 'Public can view doctors'
  ) THEN
    CREATE POLICY "Public can view doctors" ON doctors
      FOR SELECT USING (true);
  END IF;

  -- bookings policies (patient sees/inserts own; status updates go through backend service role)
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'bookings' AND policyname = 'Users can see own bookings'
  ) THEN
    CREATE POLICY "Users can see own bookings" ON bookings
      FOR SELECT USING (patient_id = auth.uid());
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'bookings' AND policyname = 'Users can create own bookings'
  ) THEN
    CREATE POLICY "Users can create own bookings" ON bookings
      FOR INSERT WITH CHECK (patient_id = auth.uid());
  END IF;
END
$$;
"""


def main():
    db_url = get_connection_string()
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
        print("✅ Sehat Sathi tables created successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
