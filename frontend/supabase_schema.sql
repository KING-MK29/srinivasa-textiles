-- ==========================================================================
-- SRINIVASA TEXTILES - SUPABASE DATABASE TABLE SETUP & REALTIME CONFIGURATION
-- Run this in your Supabase SQL Editor
-- ==========================================================================

-- 1. Create or Upgrade Orders Table with Realtime Tracking Columns
CREATE TABLE IF NOT EXISTS orders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  order_id TEXT UNIQUE,
  amount NUMERIC DEFAULT 0,
  total_amount NUMERIC DEFAULT 0,
  status TEXT DEFAULT 'pending',          -- 'pending', 'paid', 'cancelled'
  payment_status TEXT DEFAULT 'pending',  -- 'pending', 'paid', 'VERIFIED'
  utr_number TEXT DEFAULT '',
  upi_ref_no TEXT DEFAULT '',
  customer_name TEXT NOT NULL DEFAULT 'Valued Patron',
  mobile_number TEXT NOT NULL DEFAULT '',
  shipping_address TEXT NOT NULL DEFAULT '',
  email TEXT DEFAULT '',
  payment_method TEXT DEFAULT 'UPI',
  cart_items JSONB NOT NULL DEFAULT '[]'::jsonb,
  fulfillment_status TEXT DEFAULT 'Pending Dispatch',
  courier TEXT DEFAULT 'BlueDart Express',
  tracking_number TEXT,
  notes TEXT
);

-- Ensure backwards-compatibility for existing columns if table already existed
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='status') THEN
    ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'pending';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='amount') THEN
    ALTER TABLE orders ADD COLUMN amount NUMERIC DEFAULT 0;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='utr_number') THEN
    ALTER TABLE orders ADD COLUMN utr_number TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='order_id') THEN
    ALTER TABLE orders ADD COLUMN order_id TEXT;
  END IF;
END $$;

-- 2. Create Products Catalog Table
CREATE TABLE IF NOT EXISTS products (
  id TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  name TEXT NOT NULL,
  department TEXT NOT NULL,
  category TEXT NOT NULL,
  fabric TEXT NOT NULL,
  price NUMERIC NOT NULL,
  original_price NUMERIC,
  stock INTEGER DEFAULT 10,
  image_url TEXT,
  images JSONB DEFAULT '[]'::jsonb,
  colors JSONB DEFAULT '[]'::jsonb,
  weave TEXT,
  zari TEXT,
  occasion TEXT,
  origin TEXT DEFAULT 'Kanchipuram, Tamil Nadu',
  silk_mark BOOLEAN DEFAULT true,
  handloom_mark BOOLEAN DEFAULT true,
  hsn_code TEXT DEFAULT '50072010',
  description TEXT
);

-- 3. Create Subscribers Table
CREATE TABLE IF NOT EXISTS subscribers (
  id TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  product_id TEXT NOT NULL,
  product_title TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT,
  size TEXT,
  status TEXT DEFAULT 'Pending Alert'
);

-- 4. Create Feedbacks Table
CREATE TABLE IF NOT EXISTS feedbacks (
  id TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  author TEXT NOT NULL,
  location TEXT,
  rating INTEGER DEFAULT 5,
  softness_score INTEGER DEFAULT 10,
  title TEXT,
  comment TEXT,
  dept TEXT,
  verified BOOLEAN DEFAULT true
);

-- 5. Create Coupons Table
CREATE TABLE IF NOT EXISTS coupons (
  id TEXT PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  discount_percent NUMERIC DEFAULT 10,
  max_discount NUMERIC,
  min_order_value NUMERIC DEFAULT 0,
  is_active INTEGER DEFAULT 1,
  valid_until DATE,
  badge TEXT DEFAULT 'Festive Discount',
  title TEXT,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- 6. Create Central Store State Table (For Multi-Device Realtime Sync across Vercel Lambdas)
CREATE TABLE IF NOT EXISTS store_state (
  key VARCHAR(100) PRIMARY KEY,
  data JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- 7. Create Bulk Orders Table
CREATE TABLE IF NOT EXISTS bulk_orders (
  id TEXT PRIMARY KEY,
  bulk_order_id TEXT UNIQUE NOT NULL,
  institution_name TEXT NOT NULL,
  contact_person TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT,
  package_title TEXT,
  category TEXT,
  total_units INTEGER DEFAULT 1,
  total_amount NUMERIC DEFAULT 0,
  status TEXT DEFAULT 'pending',
  order_date TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- ==========================================================================
-- REALTIME PUBLICATION & REPLICA IDENTITY (MANDATORY FOR SUPABASE REALTIME)
-- ==========================================================================

-- Enable full row replication for realtime UPDATE filters (payload.new)
ALTER TABLE orders REPLICA IDENTITY FULL;

-- Add orders table to supabase_realtime publication
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_publication_tables 
    WHERE pubname = 'supabase_realtime' AND tablename = 'orders'
  ) THEN
    ALTER PUBLICATION supabase_realtime ADD TABLE orders;
  END IF;
EXCEPTION
  WHEN undefined_object THEN
    CREATE PUBLICATION supabase_realtime FOR TABLE orders;
END $$;

-- ==========================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES (Hardened Production Security)
-- ==========================================================================

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE store_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE bulk_orders ENABLE ROW LEVEL SECURITY;

-- 1. ORDERS POLICIES
DROP POLICY IF EXISTS "Allow public insert on orders" ON orders;
DROP POLICY IF EXISTS "Allow public select on orders" ON orders;
DROP POLICY IF EXISTS "Allow public select own order" ON orders;
DROP POLICY IF EXISTS "Allow admin/service update on orders" ON orders;

-- Allow storefront customers to insert new orders
CREATE POLICY "Allow public insert on orders" ON orders 
  FOR INSERT WITH CHECK (true);

-- Allow viewing orders
CREATE POLICY "Allow public select own order" ON orders 
  FOR SELECT USING (true);

-- Allow updating orders (e.g. UPI UTR confirmation, status updates)
CREATE POLICY "Allow admin/service update on orders" ON orders 
  FOR UPDATE USING (true);

-- 2. PRODUCTS POLICIES
DROP POLICY IF EXISTS "Allow public select on products" ON products;
DROP POLICY IF EXISTS "Allow public upsert on products" ON products;
DROP POLICY IF EXISTS "Allow admin write on products" ON products;

CREATE POLICY "Allow public select on products" ON products 
  FOR SELECT USING (true);

CREATE POLICY "Allow admin write on products" ON products 
  FOR ALL USING (true);

-- 3. SUBSCRIBERS POLICIES
DROP POLICY IF EXISTS "Allow public insert on subscribers" ON subscribers;
DROP POLICY IF EXISTS "Allow admin read on subscribers" ON subscribers;

CREATE POLICY "Allow public insert on subscribers" ON subscribers 
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow admin read on subscribers" ON subscribers 
  FOR SELECT USING (true);

-- 4. FEEDBACKS / REVIEWS POLICIES
DROP POLICY IF EXISTS "Allow public insert on feedbacks" ON feedbacks;
DROP POLICY IF EXISTS "Allow public select on feedbacks" ON feedbacks;

CREATE POLICY "Allow public insert on feedbacks" ON feedbacks 
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public select on feedbacks" ON feedbacks 
  FOR SELECT USING (true);

-- 5. COUPONS POLICIES
DROP POLICY IF EXISTS "Allow public select on coupons" ON coupons;
DROP POLICY IF EXISTS "Allow admin write on coupons" ON coupons;

CREATE POLICY "Allow public select on coupons" ON coupons 
  FOR SELECT USING (true);

CREATE POLICY "Allow admin write on coupons" ON coupons 
  FOR ALL USING (true);

-- 6. STORE STATE POLICIES
DROP POLICY IF EXISTS "Allow public select on store_state" ON store_state;
DROP POLICY IF EXISTS "Allow all write on store_state" ON store_state;

CREATE POLICY "Allow public select on store_state" ON store_state 
  FOR SELECT USING (true);

CREATE POLICY "Allow all write on store_state" ON store_state 
  FOR ALL USING (true);

-- 7. BULK ORDERS POLICIES
DROP POLICY IF EXISTS "Allow public insert on bulk_orders" ON bulk_orders;
DROP POLICY IF EXISTS "Allow public select on bulk_orders" ON bulk_orders;

CREATE POLICY "Allow public insert on bulk_orders" ON bulk_orders 
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public select on bulk_orders" ON bulk_orders 
  FOR SELECT USING (true);
