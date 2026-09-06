-- Sehat Sathi — Supabase Database Schema
-- Run this in Supabase SQL Editor (https://supabase.com/dashboard/project/YOUR_ID/sql/new)

-- 1. conversations table
CREATE TABLE conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. messages table
CREATE TABLE messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  route TEXT,
  severity TEXT,
  timestamp TIMESTAMPTZ DEFAULT now()
);

-- 3. Enable Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies — users can only see their own data
CREATE POLICY "Users can see own conversations" ON conversations
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create own conversations" ON conversations
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can see own messages" ON messages
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create own messages" ON messages
  FOR INSERT WITH CHECK (user_id = auth.uid());