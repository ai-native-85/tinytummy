# TinyTummy Database Schema Documentation

## 🗄️ Schema Overview

The TinyTummy database is designed to support an AI-powered baby nutrition tracker with both free and premium features. The schema is optimized for scalability, performance, and data integrity.

## 📊 Table Relationships

### Core Entity Relationships
```
users (1) ──→ (N) children
children (1) ──→ (N) meals
children (1) ──→ (N) plans (premium)
children (1) ──→ (N) reports (premium)
users (1) ──→ (N) chat_sessions
chat_sessions (1) ──→ (N) chat_messages
users (1) ──→ (1) gamification
users (M) ──→ (N) children (via caregiver_links)
```

## 🏗️ Key Design Decisions

### 1. **UUID Primary Keys**
- All tables use UUID primary keys for security and scalability
- Enables distributed systems and prevents ID enumeration attacks
- Uses `uuid-ossp` extension for UUID generation

### 2. **JSONB for Flexible Data**
- `meals.gpt_analysis`: Stores complete GPT-4 analysis results
- `plans.plan_data`: 21-day meal plan structure
- `reports.report_data`: PDF report content
- `gamification.badges`: Array of earned badges
- `chat_sessions.context_data`: Child profile and nutrition trends

### 3. **Enum Types for Data Integrity**
- `subscription_tier`: 'free' | 'premium'
- `meal_type`: 'breakfast' | 'lunch' | 'dinner' | 'snack'
- `input_method`: 'text' | 'voice' | 'image'
- `report_type`: 'weekly' | 'monthly' | 'custom'
- `badge_type`: 'streak' | 'milestone' | 'achievement' | 'social'

### 4. **Comprehensive Nutrition Tracking**
The `meals` table includes detailed nutrition fields:
- Macronutrients: calories, protein, fat, carbs, fiber
- Micronutrients: iron, calcium, vitamins A/C/D, zinc, folate
- Confidence scoring for GPT-4 analysis accuracy
- Array fields for food items and allergies

### 5. **Premium Feature Isolation**
Premium features are clearly separated:
- `plans` table for 21-day meal plans
- `reports` table for pediatrician PDF reports
- `caregiver_links` for multi-user access
- Subscription tier tracking in `users` table

## 🔐 Security Features

### Row Level Security (RLS)
All user data tables have RLS enabled:
- `users`, `children`, `meals`, `plans`, `reports`
- `chat_sessions`, `chat_messages`, `gamification`
- `caregiver_links`, `offline_sync`

### Password Security
- Uses `pgcrypto` extension for password hashing
- Passwords stored as hashes, never plaintext

## 📈 Performance Optimizations

### Strategic Indexing
- Foreign key indexes for all relationships
- Date-based indexes for meal logging and trends
- Full-text search on food items and guidelines
- Composite indexes for age-based nutrition queries

### Efficient Queries
- JSONB indexes for flexible data queries
- GIN indexes for array and full-text search
- Optimized for common query patterns

## 🤖 AI Integration Points

### GPT-4 Analysis Storage
```sql
-- meals.gpt_analysis JSONB structure
{
  "detected_foods": ["apple", "banana"],
  "estimated_quantities": {"apple": "1 medium", "banana": "1 small"},
  "nutrition_breakdown": {
    "calories": 120,
    "protein": 1.2,
    "iron": 0.3
  },
  "confidence_score": 0.85,
  "analysis_notes": "Good iron source from apple"
}
```

### RAG Integration
- `nutrition_guidelines` table stores vector embeddings
- `embedding_id` field links to Pinecone/pgvector
- Full-text search enabled for semantic queries

## 📱 Offline Support

### Sync Architecture
- `offline_sync` table tracks pending changes
- Device-specific sync data storage
- Batch sync endpoints for efficiency

## 🎮 Gamification System

### Badge System
- Predefined badges with criteria stored as JSONB
- Junction table for user-badge relationships
- Points and experience tracking

### Streak Tracking
- Current and longest streak tracking
- Activity date monitoring
- Level progression system

## 🔄 Data Flow

### Meal Logging Flow
1. User logs meal (text/voice/image)
2. GPT-4 analyzes and extracts nutrition data
3. Data stored in `meals` table with confidence score
4. Gamification updated (streaks, points)
5. Offline sync data updated

### Chat Assistant Flow
1. User query + child context
2. Fetch recent meal history
3. Query nutrition guidelines (RAG)
4. Build system prompt with context
5. GPT-4 generates personalized response
6. Store in chat_sessions/chat_messages

## 🚀 Scalability Considerations

### Horizontal Scaling
- UUID primary keys support distributed systems
- Stateless API design
- Vector DB separation for RAG

### Vertical Scaling
- Efficient indexing strategy
- JSONB for flexible schema evolution
- Partitioning ready for large datasets

## 🔧 Migration Strategy

### Version Control
- Schema changes tracked in migrations
- Backward compatibility maintained
- Zero-downtime deployment support

### Data Integrity
- Foreign key constraints with CASCADE
- Check constraints for data validation
- Triggers for automatic timestamp updates

## 📊 Analytics Ready

### Aggregation Support
- Date-based meal aggregation
- Nutrition trend analysis
- User engagement metrics
- Premium feature usage tracking

### Export Capabilities
- JSONB data export for reports
- CSV export for analytics
- PDF generation for pediatrician reports

## 🛡️ Compliance & Privacy

### GDPR Ready
- User data deletion cascades
- Audit trail via timestamps
- Data export capabilities

### HIPAA Considerations
- Child health data protection
- Caregiver access controls
- Secure data transmission

## 🔍 Query Examples

### Common Queries
```sql
-- Get child's nutrition trends (last 30 days)
SELECT 
  DATE(logged_at) as date,
  SUM(calories) as daily_calories,
  SUM(iron_mg) as daily_iron
FROM meals 
WHERE child_id = $1 
  AND logged_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(logged_at)
ORDER BY date;

-- Get user's active streaks
SELECT 
  current_streak,
  longest_streak,
  points
FROM gamification 
WHERE user_id = $1;

-- Get caregiver access for child
SELECT 
  u.email,
  cl.permissions,
  cl.status
FROM caregiver_links cl
JOIN users u ON cl.caregiver_user_id = u.id
WHERE cl.child_id = $1;
```

This schema provides a solid foundation for the TinyTummy backend, supporting all required features while maintaining performance, security, and scalability. 