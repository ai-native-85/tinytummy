# TinyTummy API - AI-powered Baby Nutrition Tracker

A comprehensive FastAPI backend for an AI-powered baby nutrition tracking application with GPT-4 integration and premium features.

## 🚀 Features

### Free Tier
- ✅ User registration and authentication (JWT)
- ✅ Single child profile management
- ✅ Meal logging with GPT-4 analysis (text, voice, image)
- ✅ Nutrition tracking and trends
- ✅ Basic gamification (streaks, badges)

### Premium Tier
- ✅ Multiple child profiles
- ✅ Caregiver sharing and collaboration
- ✅ AI-generated 21-day meal plans
- ✅ Pediatrician PDF reports
- ✅ Smart AI chat assistant with RAG
- ✅ Advanced analytics and insights

## 🏗️ Architecture

```
TinyTummy/
├── app/
│   ├── auth/           # JWT authentication
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   ├── config.py       # Settings
│   └── database.py     # Database connection
├── main.py             # FastAPI application
├── requirements.txt    # Dependencies
└── env.example        # Environment variables
```

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy
- **Authentication**: JWT with bcrypt
- **AI**: OpenAI GPT-4
- **Vector DB**: Pinecone (for RAG)
- **Documentation**: Swagger/OpenAPI

## 📋 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Children
- `POST /children/` - Create child profile
- `GET /children/` - Get user's children
- `GET /children/{id}` - Get specific child
- `PUT /children/{id}` - Update child
- `DELETE /children/{id}` - Delete child

### Meals
- `POST /meals/log` - Log meal with GPT-4 analysis
- `GET /meals/{child_id}` - Get child's meals
- `GET /meals/trends/{child_id}` - Get nutrition trends
- `POST /meals/batch-sync` - Sync offline meals

### Premium Features
- `POST /plans/generate` - Generate meal plan
- `GET /plans/{child_id}` - Get meal plans
- `POST /reports/generate` - Generate report
- `GET /reports/{child_id}` - Get reports
- `POST /chat/query` - AI chat assistant
- `GET /chat/sessions` - Get chat sessions
- `POST /caregiver/invite` - Invite caregiver
- `GET /caregiver/{child_id}/access` - Get caregiver access

### Gamification
- `GET /gamification/{user_id}` - Get user stats
- `GET /gamification/badges` - Get available badges

### Sync
- `POST /sync/` - Sync offline data
- `GET /sync/pending` - Get pending sync data

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp env.example .env
# Edit .env with your configuration
```

### 3. Database Setup
```bash
# Run the SQL schema in Supabase
# The schema is in database_schema.sql
```

### 4. Run the Application
```bash
python main.py
# Or with uvicorn
uvicorn main:app --reload
```

### 5. Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/tinytummy
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# Pinecone (for RAG)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=tinytummy-guidelines
```

## 🧠 AI Integration

### GPT-4 Meal Analysis
The API uses GPT-4 to analyze meal descriptions and extract:
- Food items and quantities
- Nutritional breakdown (calories, protein, iron, etc.)
- Confidence scores
- Analysis notes

### RAG for Chat Assistant
- Uses Pinecone vector database
- Stores nutrition guidelines and best practices
- Provides contextual responses based on child's profile

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Row Level Security (RLS) enabled
- Premium feature gating
- Input validation with Pydantic

## 📊 Database Schema

The application uses a comprehensive PostgreSQL schema with:
- 13 tables with proper relationships
- UUID primary keys for security
- JSONB fields for flexible data storage
- Automatic timestamp triggers
- Strategic indexing for performance

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## 🚀 Deployment

### Railway (current)

- Deployed from `main` branch.
- Latest change: normalize `meal_type` & `input_method` to lowercase in `MealCreate`.
- To force redeploy: push any commit to `main`.

### Render
```yaml
# render.yaml
services:
  - type: web
    name: tinytummy-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Fly.io
```bash
fly launch
fly deploy
```

## 📈 Monitoring

- Health check endpoint: `GET /health`
- Structured logging
- Error tracking
- Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For support, please open an issue on GitHub or contact the development team.

---

**TinyTummy API** - Making baby nutrition tracking smarter with AI! 🍼✨ 