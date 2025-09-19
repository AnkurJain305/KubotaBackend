-- KUBOTA PARTS AI BACKEND - COMPLETE DATABASE SETUP WITH KUBOTA INTEGRATION
-- Production-ready database schema with Kubota parts AI system

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables in correct order (reverse dependency)
DROP TABLE IF EXISTS symptom_recommendations CASCADE;
DROP TABLE IF EXISTS kubota_part_catalog CASCADE;
DROP TABLE IF EXISTS kubota_series CASCADE;
DROP TABLE IF EXISTS kubota_parts CASCADE;
DROP TABLE IF EXISTS user_feedback CASCADE;
DROP TABLE IF EXISTS system_notifications CASCADE;
DROP TABLE IF EXISTS repair_schedules CASCADE;
DROP TABLE IF EXISTS parts_requests CASCADE;
DROP TABLE IF EXISTS job_parts CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS machines CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS parts_inventory CASCADE;
DROP TABLE IF EXISTS causes CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;

-- ======================= KUBOTA SPECIFIC TABLES =======================

-- 1. Kubota Series Reference Table
CREATE TABLE kubota_series (
    series_id SERIAL PRIMARY KEY,
    series_name VARCHAR(100) UNIQUE NOT NULL,
    series_code VARCHAR(50) UNIQUE,
    description TEXT,
    machine_type VARCHAR(50), -- tractor, loader, mower, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Main Kubota Parts Table with Claim Data and Embeddings
CREATE TABLE kubota_parts (
    claim_id VARCHAR(100) PRIMARY KEY,
    series_name VARCHAR(100),
    sub_series VARCHAR(100),
    sub_assembly VARCHAR(200),
    symptom_comments TEXT,
    defect_comments TEXT,
    symptom_comments_clean TEXT,
    defect_comments_clean TEXT,
    item_name VARCHAR(500),
    part_name VARCHAR(500),
    part_quantity INTEGER,
    part_dict JSONB, -- Part number to quantity mapping
    embedding_symptom vector(1536), -- OpenAI ada-002 embeddings
    embedding_defect vector(1536), -- OpenAI ada-002 embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Kubota Parts Catalog
CREATE TABLE kubota_part_catalog (
    part_id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    part_name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- hydraulic, engine, transmission, etc.
    compatible_series TEXT[], -- Array of compatible series
    price DECIMAL(10,2),
    weight DECIMAL(8,2),
    dimensions JSONB, -- Store dimensions as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. AI Symptom Recommendations
CREATE TABLE symptom_recommendations (
    id SERIAL PRIMARY KEY,
    user_symptom TEXT NOT NULL,
    recommended_symptom TEXT NOT NULL,
    confidence_score DECIMAL(5,3) NOT NULL,
    source VARCHAR(50), -- AI, historical, manual
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================= EXISTING SYSTEM TABLES =======================

-- 5. Users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Machines (Updated to reference Kubota series)
CREATE TABLE machines (
    machine_id SERIAL PRIMARY KEY,
    machine_name VARCHAR(255) NOT NULL,
    model VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    kubota_series_id INTEGER REFERENCES kubota_series(series_id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Tickets
CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    issue_type VARCHAR(50),
    issue_text TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    priority INTEGER DEFAULT 1,
    machine_id INTEGER NOT NULL REFERENCES machines(machine_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cause_description TEXT,
    kubota_claim_id VARCHAR(100) REFERENCES kubota_parts(claim_id), -- Link to similar case
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Parts Inventory (Enhanced)
CREATE TABLE parts_inventory (
    inventory_id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    part_name VARCHAR(255) NOT NULL,
    description TEXT,
    current_stock INTEGER DEFAULT 0,
    reserved_stock INTEGER DEFAULT 0,
    minimum_stock INTEGER DEFAULT 0,
    cost DECIMAL(10,2),
    supplier VARCHAR(255),
    lead_time_days INTEGER,
    kubota_catalog_id INTEGER REFERENCES kubota_part_catalog(part_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Jobs (Enhanced with AI recommendations)
CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    scheduled_date TIMESTAMP,
    completed_date TIMESTAMP,
    ai_recommended_parts JSONB, -- AI recommended parts list
    confidence_score DECIMAL(5,3), -- AI confidence in recommendations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Job Parts
CREATE TABLE job_parts (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    part_number VARCHAR(100) NOT NULL REFERENCES parts_inventory(part_number),
    quantity_used INTEGER DEFAULT 1,
    was_ai_recommended BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Parts Requests (Enhanced)
CREATE TABLE parts_requests (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    part_number VARCHAR(100) NOT NULL REFERENCES parts_inventory(part_number),
    quantity_requested INTEGER DEFAULT 1,
    quantity_fulfilled INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    estimated_arrival TIMESTAMP,
    notes TEXT,
    recommended_by_ai BOOLEAN DEFAULT FALSE,
    ai_confidence DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Repair Schedules
CREATE TABLE repair_schedules (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER UNIQUE NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    scheduled_date TIMESTAMP,
    estimated_duration INTEGER,
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. System Notifications (Enhanced)
CREATE TABLE system_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticket_id INTEGER REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 1,
    data JSONB,
    ai_generated BOOLEAN DEFAULT FALSE, -- Flag for AI-generated notifications
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. User Feedback
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    feedback_type VARCHAR(100) NOT NULL,
    rating INTEGER,
    comments TEXT,
    specific_data JSONB,
    ai_accuracy_rating INTEGER, -- User rating of AI recommendations (1-5)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. Causes
CREATE TABLE causes (
    cause_id SERIAL PRIMARY KEY,
    cause_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. Legacy Notifications
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'general',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================= CREATE INDEXES FOR PERFORMANCE =======================

-- Standard indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_machines_user_id ON machines(user_id);
CREATE INDEX idx_machines_series ON machines(kubota_series_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_user_id ON tickets(user_id);
CREATE INDEX idx_tickets_machine_id ON tickets(machine_id);
CREATE INDEX idx_tickets_claim_id ON tickets(kubota_claim_id);
CREATE INDEX idx_jobs_ticket_id ON jobs(ticket_id);
CREATE INDEX idx_jobs_technician_id ON jobs(technician_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_parts_inventory_part_number ON parts_inventory(part_number);
CREATE INDEX idx_parts_requests_ticket_id ON parts_requests(ticket_id);
CREATE INDEX idx_parts_requests_part_number ON parts_requests(part_number);
CREATE INDEX idx_system_notifications_user_id ON system_notifications(user_id);
CREATE INDEX idx_system_notifications_is_read ON system_notifications(is_read);

-- Kubota-specific indexes
CREATE INDEX idx_kubota_parts_series ON kubota_parts(series_name);
CREATE INDEX idx_kubota_parts_assembly ON kubota_parts(sub_assembly);
CREATE INDEX idx_kubota_part_catalog_number ON kubota_part_catalog(part_number);
CREATE INDEX idx_kubota_part_catalog_category ON kubota_part_catalog(category);
CREATE INDEX idx_symptom_recommendations_symptom ON symptom_recommendations(user_symptom);

-- Vector indexes for AI similarity search (requires pgvector)
CREATE INDEX idx_kubota_parts_symptom_embedding ON kubota_parts USING ivfflat (embedding_symptom vector_cosine_ops);
CREATE INDEX idx_kubota_parts_defect_embedding ON kubota_parts USING ivfflat (embedding_defect vector_cosine_ops);

-- GIN indexes for JSON fields
CREATE INDEX idx_kubota_parts_part_dict ON kubota_parts USING gin(part_dict);
CREATE INDEX idx_jobs_ai_parts ON jobs USING gin(ai_recommended_parts);
CREATE INDEX idx_kubota_part_catalog_compat ON kubota_part_catalog USING gin(compatible_series);

-- ======================= INSERT REFERENCE DATA =======================

-- Insert Kubota Series
INSERT INTO kubota_series (series_name, series_code, description, machine_type) VALUES
('L3901HST', 'L3901', 'Compact utility tractor with HST transmission', 'tractor'),
('L4701HST', 'L4701', 'Mid-size utility tractor with HST transmission', 'tractor'),
('M5-091', 'M5091', 'Mid-size tractor for agricultural applications', 'tractor'),
('M5-111', 'M5111', 'Mid-size tractor with increased horsepower', 'tractor'),
('B2650HSD', 'B2650', 'Sub-compact tractor with mid-mount mower', 'tractor'),
('BX2380', 'BX2380', 'Sub-compact tractor for residential use', 'tractor'),
('LX2610SU', 'LX2610', 'Compact utility tractor with loader', 'tractor'),
('MX5200', 'MX5200', 'Utility tractor for farm operations', 'tractor'),
('L6060HST', 'L6060', 'Large utility tractor with advanced features', 'tractor'),
('B3350SU', 'B3350', 'Sub-compact tractor with versatile implements', 'tractor');

-- Insert sample users
INSERT INTO users (name, email, phone, address) VALUES
('John Smith', 'john.smith@farmtest.com', '+1-555-FARM-001', '123 Rural Road, Farmtown, ST 12345'),
('Jane Farmer', 'jane.farmer@agriculture.com', '+1-555-FARM-002', '456 Country Lane, Cropville, ST 67890'),
('Mike Technician', 'mike.tech@kubota.com', '+1-555-TECH-001', '789 Service Blvd, Techtown, ST 11111'),
('Sarah Manager', 'sarah.manager@kubota.com', '+1-555-MGR-001', '100 Corporate Ave, Business City, ST 22222'),
('Bob Rancher', 'bob.rancher@cattle.com', '+1-555-RANCH-001', '200 Prairie View, Ranchland, ST 33333');

-- Insert sample machines linked to series
INSERT INTO machines (machine_name, model, serial_number, user_id, kubota_series_id, description) VALUES
('Johns L3901 Tractor', 'L3901HST', 'L3901-2024-001', 1, 1, 'Primary farming tractor for field work'),
('Janes M5 Tractor', 'M5-091', 'M5091-2024-002', 2, 3, 'Agricultural tractor for crop management'),
('Johns Compact Mower', 'B2650HSD', 'B2650-2024-003', 1, 5, 'Compact tractor with mid-mount mower deck'),
('Bobs Utility Tractor', 'L4701HST', 'L4701-2024-004', 5, 2, 'Heavy-duty utility tractor for ranch work'),
('Farm Co Main Tractor', 'M5-111', 'M5111-2024-005', 2, 4, 'Primary tractor for large-scale farming');

-- Insert Kubota parts catalog
INSERT INTO kubota_part_catalog (part_number, part_name, description, category, compatible_series, price, weight) VALUES
('7J065-85200', 'Hydraulic Valve Block Assembly', 'Main hydraulic valve block for loader operations', 'hydraulic', ARRAY['L3901HST', 'L4701HST', 'M5-091'], 245.00, 8.5),
('8K110-12345', 'Hydraulic Filter Element', 'High-flow hydraulic filter for all Kubota models', 'hydraulic', ARRAY['L3901HST', 'L4701HST', 'M5-091', 'M5-111'], 35.50, 1.2),
('7J065-85030', 'Hydraulic Pump Seal Kit', 'Complete seal kit for hydraulic pumps', 'hydraulic', ARRAY['L3901HST', 'M5-091'], 67.25, 0.8),
('9L200-54321', 'Quick Coupler Assembly', 'Hydraulic quick coupler for implements', 'hydraulic', ARRAY['L3901HST', 'L4701HST', 'M5-091', 'M5-111'], 125.00, 3.2),
('7J065-85100', 'Hydraulic Hose Assembly', 'High-pressure hydraulic hose for outlet block', 'hydraulic', ARRAY['L3901HST', 'M5-091'], 85.75, 2.1),
('4K123-55667', 'Engine Oil Filter', 'Premium oil filter for diesel engines', 'engine', ARRAY['L3901HST', 'L4701HST', 'M5-091', 'M5-111', 'B2650HSD'], 18.75, 0.4),
('2L455-99888', 'Air Filter Element', 'Heavy-duty air filter for dusty conditions', 'engine', ARRAY['L3901HST', 'L4701HST', 'M5-091'], 42.30, 0.6),
('1A111-22333', 'Fuel Filter Assembly', 'Water-separating fuel filter', 'engine', ARRAY['L3901HST', 'L4701HST', 'M5-091', 'M5-111'], 28.90, 0.3),
('5N777-88999', 'HST Transmission Filter', 'Hydrostatic transmission filter', 'transmission', ARRAY['L3901HST', 'L4701HST', 'B2650HSD'], 52.15, 0.7),
('3P888-11222', 'Transmission Oil Seal', 'Main transmission oil seal', 'transmission', ARRAY['M5-091', 'M5-111'], 34.50, 0.2);

-- Insert parts inventory linked to catalog
INSERT INTO parts_inventory (part_number, part_name, description, current_stock, minimum_stock, cost, supplier, lead_time_days, kubota_catalog_id) VALUES
('7J065-85200', 'Hydraulic Valve Block Assembly', 'Main hydraulic valve block for L3901 series', 5, 2, 245.00, 'Kubota Direct', 7, 1),
('8K110-12345', 'Hydraulic Filter Element', 'High-flow hydraulic filter for all models', 15, 5, 35.50, 'Kubota Direct', 3, 2),
('7J065-85030', 'Hydraulic Pump Seal Kit', 'Complete seal kit for hydraulic pumps', 12, 3, 67.25, 'Kubota Direct', 4, 3),
('9L200-54321', 'Quick Coupler Assembly', 'Hydraulic quick coupler for implements', 8, 2, 125.00, 'Kubota Direct', 5, 4),
('7J065-85100', 'Hydraulic Hose Assembly', 'High-pressure hydraulic hose', 10, 3, 85.75, 'Kubota Direct', 4, 5),
('4K123-55667', 'Engine Oil Filter', 'Premium oil filter for diesel engines', 25, 10, 18.75, 'Kubota Direct', 2, 6),
('2L455-99888', 'Air Filter Element', 'Heavy-duty air filter for dusty conditions', 20, 8, 42.30, 'Kubota Direct', 2, 7),
('1A111-22333', 'Fuel Filter Assembly', 'Water-separating fuel filter', 18, 6, 28.90, 'Kubota Direct', 3, 8),
('5N777-88999', 'HST Transmission Filter', 'Hydrostatic transmission filter', 8, 4, 52.15, 'Kubota Direct', 5, 9),
('3P888-11222', 'Transmission Oil Seal', 'Main transmission oil seal', 15, 5, 34.50, 'Kubota Direct', 3, 10);

-- Insert sample causes
INSERT INTO causes (cause_name, description, category) VALUES
('Hydraulic System Low Pressure', 'Hydraulic system not generating sufficient pressure for operation', 'hydraulic'),
('Engine Oil Contamination', 'Engine oil contaminated with debris or water', 'engine'),
('Air Filter Clogged', 'Air filter severely clogged reducing engine performance', 'engine'),
('HST Transmission Overheating', 'Hydrostatic transmission running too hot during operation', 'transmission'),
('Electrical System Fault', 'Electrical components not functioning properly', 'electrical'),
('Cooling System Issues', 'Engine cooling system not maintaining proper temperature', 'cooling'),
('Hydraulic Seal Failure', 'Hydraulic seals deteriorated causing fluid leaks', 'hydraulic'),
('Fuel Contamination', 'Fuel system contaminated with water or debris', 'engine'),
('Quick Coupler Malfunction', 'Quick coupler not engaging or releasing properly', 'hydraulic'),
('Transmission Filter Clogged', 'HST transmission filter needs replacement', 'transmission');

-- Insert sample tickets with AI linkage
INSERT INTO tickets (issue_type, issue_text, status, priority, machine_id, user_id, cause_description) VALUES
('hydraulic', 'My L3901 tractor hydraulic system has very low pressure when lifting implements. The loader barely lifts and makes strange noises.', 'open', 3, 1, 1, 'Hydraulic system low pressure - possible valve block or filter issue'),
('engine', 'Engine on my M5-091 is running rough with black smoke from exhaust. Performance has decreased significantly.', 'open', 2, 2, 2, 'Engine performance issues - likely air filter or fuel system contamination'),
('transmission', 'HST transmission on my B2650 is making grinding noises and getting very hot during operation.', 'in_progress', 2, 3, 1, 'HST transmission overheating - filter or oil issue'),
('hydraulic', 'Quick coupler on my L4701 is leaking hydraulic fluid and won''t engage properly with implements.', 'open', 3, 4, 5, 'Quick coupler malfunction - seal replacement needed'),
('engine', 'My M5-111 tractor engine is hard to start and runs rough. Fuel filter warning light is on.', 'open', 2, 5, 2, 'Fuel system issues - filter replacement required');

-- Insert sample jobs with AI recommendations
INSERT INTO jobs (ticket_id, technician_id, status, scheduled_date, ai_recommended_parts, confidence_score) VALUES
(1, 3, 'scheduled', '2025-09-19 10:00:00', 
 '{"recommended_parts": ["7J065-85200", "8K110-12345"], "confidence": 0.85, "reasoning": "High probability hydraulic valve and filter replacement"}', 0.85),
(2, 3, 'in_progress', '2025-09-18 14:00:00',
 '{"recommended_parts": ["2L455-99888", "1A111-22333"], "confidence": 0.78, "reasoning": "Air and fuel filter replacement for engine issues"}', 0.78),
(3, 3, 'scheduled', '2025-09-20 09:00:00',
 '{"recommended_parts": ["5N777-88999", "3P888-11222"], "confidence": 0.82, "reasoning": "HST transmission filter and seal replacement"}', 0.82);

-- Insert sample parts requests with AI flags
INSERT INTO parts_requests (ticket_id, part_number, quantity_requested, status, priority, notes, recommended_by_ai, ai_confidence) VALUES
(1, '7J065-85200', 1, 'approved', 3, 'High priority - customer waiting for repair', TRUE, 0.85),
(1, '8K110-12345', 1, 'approved', 3, 'Replace hydraulic filter with valve block', TRUE, 0.85),
(2, '2L455-99888', 1, 'approved', 2, 'Air filter replacement for engine performance', TRUE, 0.78),
(2, '1A111-22333', 1, 'approved', 2, 'Fuel filter for contamination issue', TRUE, 0.78),
(3, '5N777-88999', 1, 'pending', 2, 'HST transmission filter replacement', TRUE, 0.82),
(4, '9L200-54321', 1, 'approved', 3, 'Quick coupler assembly replacement', TRUE, 0.90),
(5, '1A111-22333', 1, 'approved', 2, 'Fuel filter for starting issues', TRUE, 0.75);

-- Insert sample system notifications with AI flags
INSERT INTO system_notifications (user_id, ticket_id, notification_type, title, message, priority, ai_generated) VALUES
(1, 1, 'ticket_created', 'Service Ticket Created', 'Your L3901 hydraulic issue has been logged. Our AI system has identified likely causes and recommended parts.', 2, TRUE),
(1, 1, 'parts_recommended', 'AI Parts Analysis', 'AI analysis suggests hydraulic valve block and filter replacement with 85% confidence.', 2, TRUE),
(3, 1, 'job_assigned', 'Job Assignment', 'You have been assigned to service ticket #1 - L3901 hydraulic system issue. AI parts recommendations available.', 3, TRUE),
(2, 2, 'ticket_created', 'Service Ticket Created', 'Your M5-091 engine issue has been analyzed. AI recommends air and fuel filter replacement.', 2, TRUE),
(5, 4, 'parts_recommended', 'AI Parts Analysis', 'Quick coupler issue identified. AI recommends part replacement with 90% confidence.', 2, TRUE);

COMMIT;

-- Display setup completion message
SELECT 
    'Kubota Parts AI Database setup completed successfully!' as status,
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM kubota_series) as kubota_series,
    (SELECT COUNT(*) FROM kubota_part_catalog) as catalog_parts,
    (SELECT COUNT(*) FROM parts_inventory) as inventory_parts,
    (SELECT COUNT(*) FROM tickets) as total_tickets,
    (SELECT COUNT(*) FROM jobs) as total_jobs,
    'AI-ready system with embeddings support' as ai_features;
