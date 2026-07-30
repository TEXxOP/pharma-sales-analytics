-- ============================================================
-- Pharma Sales Analytics — Database Schema
-- ============================================================
-- Normalized schema for a pharmaceutical sales tracking system.
-- 5 tables covering territories, sales reps, products,
-- physicians, and sales transactions.
-- ============================================================

-- Drop tables in reverse dependency order (idempotent re-runs)
DROP TABLE IF EXISTS sales      CASCADE;
DROP TABLE IF EXISTS physicians  CASCADE;
DROP TABLE IF EXISTS reps        CASCADE;
DROP TABLE IF EXISTS products    CASCADE;
DROP TABLE IF EXISTS territories CASCADE;

-- ============================================================
-- 1. TERRITORIES — Geographic sales regions
-- ============================================================
CREATE TABLE territories (
    territory_id  SERIAL       PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    region        VARCHAR(20)  NOT NULL CHECK (region IN ('North', 'South', 'East', 'West')),
    manager       VARCHAR(100) NOT NULL
);

COMMENT ON TABLE territories IS 'Geographic sales territories grouped into 4 regions';

-- ============================================================
-- 2. REPS — Sales representatives assigned to territories
-- ============================================================
CREATE TABLE reps (
    rep_id        SERIAL        PRIMARY KEY,
    name          VARCHAR(100)  NOT NULL,
    territory_id  INT           NOT NULL REFERENCES territories(territory_id),
    hire_date     DATE          NOT NULL,
    target_quota  DECIMAL(12,2) NOT NULL CHECK (target_quota > 0)
);

CREATE INDEX idx_reps_territory ON reps(territory_id);

COMMENT ON TABLE reps IS 'Pharmaceutical sales representatives with annual quota targets';

-- ============================================================
-- 3. PRODUCTS — Pharmaceutical drugs across therapeutic areas
-- ============================================================
CREATE TABLE products (
    product_id     SERIAL        PRIMARY KEY,
    name           VARCHAR(150)  NOT NULL,
    category       VARCHAR(50)   NOT NULL CHECK (category IN ('Cardiology', 'Oncology', 'Neurology')),
    price_per_unit DECIMAL(10,2) NOT NULL CHECK (price_per_unit > 0),
    launch_date    DATE          NOT NULL
);

COMMENT ON TABLE products IS 'Drug catalog with therapeutic category and per-unit pricing';

-- ============================================================
-- 4. PHYSICIANS — Prescribing doctors targeted by reps
-- ============================================================
CREATE TABLE physicians (
    physician_id        SERIAL       PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    specialty           VARCHAR(50)  NOT NULL,
    territory_id        INT          NOT NULL REFERENCES territories(territory_id),
    tier                CHAR(1)      NOT NULL CHECK (tier IN ('A', 'B', 'C')),
    hospital_affiliation VARCHAR(200) NOT NULL
);

CREATE INDEX idx_physicians_territory ON physicians(territory_id);
CREATE INDEX idx_physicians_tier      ON physicians(tier);

COMMENT ON TABLE physicians IS 'Target physicians with ABC tiering based on prescribing potential';

-- ============================================================
-- 5. SALES — Individual sales transactions
-- ============================================================
CREATE TABLE sales (
    sale_id      SERIAL        PRIMARY KEY,
    rep_id       INT           NOT NULL REFERENCES reps(rep_id),
    physician_id INT           NOT NULL REFERENCES physicians(physician_id),
    product_id   INT           NOT NULL REFERENCES products(product_id),
    quantity     INT           NOT NULL CHECK (quantity > 0),
    sale_date    DATE          NOT NULL,
    amount       DECIMAL(12,2) NOT NULL CHECK (amount > 0)
);

CREATE INDEX idx_sales_rep       ON sales(rep_id);
CREATE INDEX idx_sales_physician ON sales(physician_id);
CREATE INDEX idx_sales_product   ON sales(product_id);
CREATE INDEX idx_sales_date      ON sales(sale_date);

COMMENT ON TABLE sales IS 'Transactional sales records linking reps, physicians, and products';
