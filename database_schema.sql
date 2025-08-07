-- TinyTummy Database Schema
-- AI-powered Baby Nutrition Tracker

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum types
CREATE TYPE subscription_tier AS ENUM ('free', 'premium');
CREATE TYPE meal_type AS ENUM ('breakfast', 'lunch', 'dinner', 'snack');
CREATE TYPE input_method AS ENUM ('text', 'voice', 'image');
CREATE TYPE report_type AS ENUM ('weekly', 'monthly', 'custom');
CREATE TYPE badge_type AS ENUM ('streak', 'milestone', 'achievement', 'social');
CREATE TYPE guideline_type AS ENUM ('growth', 'nutrition', 'development', 'feeding', 'allergies');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    subscription_tier subscription_tier DEFAULT 'free',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Children table
CREATE TABLE children (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    weight_kg DECIMAL(5,2),
    height_cm DECIMAL(5,2),
    allergies TEXT[],
    dietary_restrictions TEXT[],
    region VARCHAR(100),
    pediatrician_name VARCHAR(255),
    pediatrician_contact VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Meals table
CREATE TABLE meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_type meal_type NOT NULL,
    meal_time TIMESTAMP WITH TIME ZONE NOT NULL, -- When the meal was consumed
    meal_date DATE, -- Regular column for date-based queries (populated by trigger)
    input_method input_method NOT NULL,
    raw_input TEXT NOT NULL,
    gpt_analysis JSONB NOT NULL, -- Stores GPT-4 analysis results
    food_items TEXT[] NOT NULL,
    estimated_quantity TEXT,
    calories DECIMAL(8,2),
    protein_g DECIMAL(6,2),
    fat_g DECIMAL(6,2),
    carbs_g DECIMAL(6,2),
    fiber_g DECIMAL(6,2),
    iron_mg DECIMAL(6,2),
    calcium_mg DECIMAL(6,2),
    vitamin_a_iu DECIMAL(8,2),
    vitamin_c_mg DECIMAL(6,2),
    vitamin_d_iu DECIMAL(8,2),
    zinc_mg DECIMAL(6,2),
    folate_mcg DECIMAL(6,2),
    confidence_score DECIMAL(3,2), -- GPT confidence in analysis
    notes TEXT,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Meal plans table (Premium feature)
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    plan_data JSONB NOT NULL, -- 21-day meal plan structure
    gpt_generation_prompt TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reports table (Premium feature)
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_type report_type NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    report_data JSONB NOT NULL, -- PDF report content
    pdf_url VARCHAR(500),
    insights TEXT[],
    recommendations TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    session_name VARCHAR(255),
    context_data JSONB, -- Child profile, nutrition trends, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB, -- RAG context, guidelines used, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gamification table
CREATE TABLE gamification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    points INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    badges JSONB DEFAULT '[]', -- Array of earned badges
    level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Badges table
CREATE TABLE badges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    badge_type badge_type NOT NULL,
    icon_url VARCHAR(500),
    points_reward INTEGER DEFAULT 0,
    criteria JSONB NOT NULL, -- Conditions to earn badge
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User badges junction table
CREATE TABLE user_badges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, badge_id)
);

-- Caregiver links table (Premium feature)
CREATE TABLE caregiver_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    primary_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    caregiver_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permissions JSONB DEFAULT '{"read": true, "write": false}', -- Read/write permissions
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined')),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(child_id, caregiver_user_id)
);

-- Nutrition guidelines table (for RAG) - FIXED STRUCTURE
CREATE TABLE nutrition_guidelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    guideline_text TEXT NOT NULL, -- Main content for embedding
    source VARCHAR(255) NOT NULL, -- WHO, AAP, local guidelines, etc.
    region VARCHAR(100), -- Geographic region (US, EU, Asia, etc.)
    language VARCHAR(10) DEFAULT 'en', -- Language code
    age_min_months INTEGER, -- Minimum age in months
    age_max_months INTEGER, -- Maximum age in months
    guideline_type guideline_type NOT NULL, -- growth, nutrition, development, feeding, allergies
    embedding_id VARCHAR(255), -- Pinecone vector ID
    metadata JSONB DEFAULT '{}', -- Additional metadata (tags, keywords, etc.)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Offline sync table
CREATE TABLE offline_sync (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    sync_data JSONB NOT NULL, -- Pending changes to sync
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_children_user_id ON children(user_id);
CREATE INDEX idx_meals_child_id ON meals(child_id);
CREATE INDEX idx_meals_user_id ON meals(user_id);
CREATE INDEX idx_meals_logged_at ON meals(logged_at);
CREATE INDEX idx_meals_meal_time ON meals(meal_time);
CREATE INDEX idx_meals_meal_date ON meals(meal_date);
CREATE INDEX idx_meals_meal_type ON meals(meal_type);
CREATE INDEX idx_meals_input_method ON meals(input_method);
CREATE INDEX idx_plans_child_id ON plans(child_id);
CREATE INDEX idx_plans_user_id ON plans(user_id);
CREATE INDEX idx_reports_child_id ON reports(child_id);
CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_gamification_user_id ON gamification(user_id);
CREATE INDEX idx_caregiver_links_child_id ON caregiver_links(child_id);
CREATE INDEX idx_caregiver_links_caregiver_user_id ON caregiver_links(caregiver_user_id);
CREATE INDEX idx_nutrition_guidelines_region ON nutrition_guidelines(region);
CREATE INDEX idx_nutrition_guidelines_age ON nutrition_guidelines(age_min_months, age_max_months);
CREATE INDEX idx_nutrition_guidelines_type ON nutrition_guidelines(guideline_type);
CREATE INDEX idx_nutrition_guidelines_language ON nutrition_guidelines(language);
CREATE INDEX idx_nutrition_guidelines_active ON nutrition_guidelines(is_active);

-- Full-text search indexes
CREATE INDEX idx_meals_food_items_gin ON meals USING GIN(food_items);
CREATE INDEX idx_nutrition_guidelines_text_gin ON nutrition_guidelines USING GIN(to_tsvector('english', guideline_text));
CREATE INDEX idx_nutrition_guidelines_title_gin ON nutrition_guidelines USING GIN(to_tsvector('english', title));

-- JSONB indexes for flexible queries
CREATE INDEX idx_meals_gpt_analysis_gin ON meals USING GIN(gpt_analysis);
CREATE INDEX idx_plans_plan_data_gin ON plans USING GIN(plan_data);
CREATE INDEX idx_reports_report_data_gin ON reports USING GIN(report_data);
CREATE INDEX idx_chat_sessions_context_data_gin ON chat_sessions USING GIN(context_data);
CREATE INDEX idx_chat_messages_metadata_gin ON chat_messages USING GIN(metadata);
CREATE INDEX idx_gamification_badges_gin ON gamification USING GIN(badges);
CREATE INDEX idx_caregiver_links_permissions_gin ON caregiver_links USING GIN(permissions);
CREATE INDEX idx_nutrition_guidelines_metadata_gin ON nutrition_guidelines USING GIN(metadata);

-- Composite indexes for common query patterns
CREATE INDEX idx_meals_child_date ON meals(child_id, meal_date);
CREATE INDEX idx_meals_user_date ON meals(user_id, meal_date);
CREATE INDEX idx_nutrition_guidelines_region_age ON nutrition_guidelines(region, age_min_months, age_max_months);
CREATE INDEX idx_nutrition_guidelines_type_region ON nutrition_guidelines(guideline_type, region);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to populate meal_date from meal_time
CREATE OR REPLACE FUNCTION update_meal_date()
RETURNS TRIGGER AS $$
BEGIN
    NEW.meal_date = NEW.meal_time::DATE;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_children_updated_at BEFORE UPDATE ON children FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_meals_updated_at BEFORE UPDATE ON meals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plans_updated_at BEFORE UPDATE ON plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_gamification_updated_at BEFORE UPDATE ON gamification FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_caregiver_links_updated_at BEFORE UPDATE ON caregiver_links FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_nutrition_guidelines_updated_at BEFORE UPDATE ON nutrition_guidelines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_offline_sync_updated_at BEFORE UPDATE ON offline_sync FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply meal_date trigger to meals table
CREATE TRIGGER update_meals_meal_date BEFORE INSERT OR UPDATE ON meals FOR EACH ROW EXECUTE FUNCTION update_meal_date();

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE children ENABLE ROW LEVEL SECURITY;
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE gamification ENABLE ROW LEVEL SECURITY;
ALTER TABLE badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE caregiver_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_guidelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE offline_sync ENABLE ROW LEVEL SECURITY;

-- Sample data for badges
INSERT INTO badges (name, description, badge_type, points_reward, criteria) VALUES
('First Meal', 'Logged your first meal', 'milestone', 10, '{"meals_logged": 1}'),
('Week Warrior', 'Logged meals for 7 consecutive days', 'streak', 50, '{"streak_days": 7}'),
('Nutrition Expert', 'Logged 100 meals', 'achievement', 200, '{"total_meals": 100}'),
('Iron Champion', 'Met iron targets for 30 days', 'achievement', 150, '{"iron_target_days": 30}'),
('Growth Tracker', 'Updated child measurements 5 times', 'milestone', 25, '{"measurement_updates": 5}'),
('Voice Logger', 'Logged 10 meals using voice input', 'achievement', 30, '{"voice_meals": 10}'),
('Image Analyzer', 'Logged 5 meals using image input', 'achievement', 40, '{"image_meals": 5}');

-- Sample nutrition guidelines data
INSERT INTO nutrition_guidelines (title, guideline_text, source, region, language, age_min_months, age_max_months, guideline_type, metadata) VALUES
('Iron Requirements for 6-12 Months', 'Infants 6-12 months need 11mg of iron daily. Good sources include iron-fortified cereals, pureed meats, and legumes. Vitamin C helps with iron absorption.', 'WHO', 'Global', 'en', 6, 12, 'nutrition', '{"nutrients": ["iron"], "foods": ["cereals", "meat", "legumes"]}'),
('Introduction of Solid Foods', 'Start with single-ingredient foods like rice cereal, pureed fruits and vegetables. Introduce one new food every 3-5 days to monitor for allergies.', 'AAP', 'US', 'en', 4, 6, 'feeding', '{"foods": ["cereals", "fruits", "vegetables"], "timing": "4-6 months"}'),
('Vitamin D Requirements', 'Infants need 400 IU of vitamin D daily. Breastfed infants should receive vitamin D supplements as breast milk is low in vitamin D.', 'WHO', 'Global', 'en', 0, 12, 'nutrition', '{"nutrients": ["vitamin_d"], "supplements": true}'),
('Food Allergy Prevention', 'Introduce common allergens like peanuts, eggs, and fish early (4-6 months) to reduce allergy risk. Start with small amounts and monitor for reactions.', 'AAP', 'US', 'en', 4, 12, 'allergies', '{"allergens": ["peanuts", "eggs", "fish"], "timing": "4-6 months"}'),
('Growth Monitoring', 'Monitor weight, length, and head circumference monthly for the first 6 months, then every 2-3 months until 12 months. Plot measurements on WHO growth charts.', 'WHO', 'Global', 'en', 0, 12, 'growth', '{"measurements": ["weight", "length", "head_circumference"], "frequency": "monthly"}');

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts with subscription tiers';
COMMENT ON TABLE children IS 'Child profiles linked to users';
COMMENT ON TABLE meals IS 'Meal logs with GPT-4 nutrition analysis';
COMMENT ON TABLE plans IS 'AI-generated 21-day meal plans (premium)';
COMMENT ON TABLE reports IS 'Pediatrician PDF reports (premium)';
COMMENT ON TABLE chat_sessions IS 'AI chat assistant sessions';
COMMENT ON TABLE gamification IS 'User points, streaks, and badges';
COMMENT ON TABLE caregiver_links IS 'Multi-user access to child profiles (premium)';
COMMENT ON TABLE nutrition_guidelines IS 'Vector embeddings for RAG in chat assistant';
COMMENT ON TABLE offline_sync IS 'Offline data synchronization';

-- Additional constraints and validations
ALTER TABLE meals ADD CONSTRAINT check_confidence_score CHECK (confidence_score >= 0 AND confidence_score <= 1);
ALTER TABLE meals ADD CONSTRAINT check_positive_nutrition CHECK (
    calories >= 0 AND protein_g >= 0 AND fat_g >= 0 AND carbs_g >= 0 AND 
    fiber_g >= 0 AND iron_mg >= 0 AND calcium_mg >= 0 AND 
    vitamin_a_iu >= 0 AND vitamin_c_mg >= 0 AND vitamin_d_iu >= 0 AND 
    zinc_mg >= 0 AND folate_mcg >= 0
);
ALTER TABLE children ADD CONSTRAINT check_positive_measurements CHECK (
    (weight_kg IS NULL OR weight_kg > 0) AND 
    (height_cm IS NULL OR height_cm > 0)
);
ALTER TABLE nutrition_guidelines ADD CONSTRAINT check_age_range CHECK (
    (age_min_months IS NULL OR age_min_months >= 0) AND
    (age_max_months IS NULL OR age_max_months >= 0) AND
    (age_min_months IS NULL OR age_max_months IS NULL OR age_min_months <= age_max_months)
); 