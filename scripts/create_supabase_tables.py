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
        print("Copy the connection string from Supabase Settings → Database")
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

-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

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
