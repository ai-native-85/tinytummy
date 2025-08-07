# TinyTummy Backend Architecture

## 🏗️ Overview

TinyTummy is an AI-powered baby nutrition tracker with a modular FastAPI backend. The system integrates GPT-4 for meal analysis, RAG for contextual chat assistance, and comprehensive gamification features.

## 📁 Directory Structure

```
TinyTummy/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Settings and environment configuration
│   ├── database.py            # Database connection and session management
│   ├── auth/
│   │   ├── __init__.py
│   │   └── jwt.py            # JWT authentication utilities
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── child.py
│   │   ├── meal.py
│   │   ├── plan.py
│   │   ├── report.py
│   │   ├── chat.py
│   │   ├── gamification.py
│   │   ├── caregiver.py
│   │   ├── nutrition.py
│   │   └── sync.py
│   ├── schemas/              # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── child.py
│   │   ├── meal.py
│   │   ├── plan.py
│   │   ├── report.py
│   │   ├── chat.py
│   │   ├── gamification.py
│   │   ├── caregiver.py
│   │   └── sync.py
│   ├── routes/               # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── children.py
│   │   ├── meals.py
│   │   ├── plans.py
│   │   ├── reports.py
│   │   ├── chat.py
│   │   ├── gamification.py
│   │   ├── caregiver.py
│   │   └── sync.py
│   ├── services/             # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── meal_service.py
│   │   ├── rag_service.py
│   │   ├── chat_service.py
│   │   ├── plan_service.py
│   │   ├── report_service.py
│   │   ├── gamification_service.py
│   │   ├── caregiver_service.py
│   │   └── sync_service.py
│   └── utils/               # Utility functions and constants
│       ├── __init__.py
│       ├── constants.py
│       ├── prompts.py
│       └── responses.py
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_meals.py
│   └── test_integration.py
├── scripts/
│   └── test_all.sh
├── main.py                  # Application entry point
├── requirements.txt
├── .env.example
├── README.md
└── ARCHITECTURE.md
```

## 🔧 Key Services

### Authentication Service (`auth_service.py`)
- **Purpose**: User registration, login, and JWT token management
- **Features**: 
  - Password hashing with bcrypt
  - JWT token generation and validation
  - User profile management
- **Dependencies**: `passlib`, `python-jose`

### Meal Service (`meal_service.py`)
- **Purpose**: Meal logging and GPT-4 nutrition analysis
- **Features**:
  - GPT-4 integration for food detection and nutrition calculation
  - Support for text, voice, and image input
  - Nutrition breakdown (calories, protein, vitamins, etc.)
  - Meal history and trends
- **Dependencies**: `openai`, SQLAlchemy

### RAG Service (`rag_service.py`)
- **Purpose**: Retrieval-Augmented Generation for contextual chat
- **Features**:
  - Pinecone vector database integration
  - Nutrition guidelines retrieval
  - Child-specific context building
  - GPT-4 response generation
- **Dependencies**: `pinecone-client`, `openai`

### Chat Service (`chat_service.py`)
- **Purpose**: Chat session and message management
- **Features**:
  - Chat session creation and management
  - Message storage and retrieval
  - Session history
- **Dependencies**: SQLAlchemy

### Plan Service (`plan_service.py`)
- **Purpose**: 21-day meal plan generation
- **Features**:
  - GPT-4 powered meal plan creation
  - Child-specific customization
  - Plan history and updates
- **Dependencies**: `openai`

### Gamification Service (`gamification_service.py`)
- **Purpose**: User engagement and rewards
- **Features**:
  - Streak tracking
  - Badge system
  - Points and levels
  - Leaderboards
- **Dependencies**: SQLAlchemy

### Caregiver Service (`caregiver_service.py`)
- **Purpose**: Multi-user access management
- **Features**:
  - Caregiver invitations
  - Permission management
  - Access control
- **Dependencies**: SQLAlchemy

### Sync Service (`sync_service.py`)
- **Purpose**: Offline data synchronization
- **Features**:
  - Offline meal logging
  - Data conflict resolution
  - Sync status tracking
- **Dependencies**: SQLAlchemy

## 🗄️ Database Schema

### Core Tables
- **users**: User accounts and subscription tiers
- **children**: Child profiles and preferences
- **meals**: Meal logs with GPT analysis
- **plans**: Generated meal plans
- **reports**: Nutrition reports
- **chat_sessions**: Chat conversation sessions
- **chat_messages**: Individual chat messages
- **gamification**: User progress and streaks
- **badges**: Available badges
- **user_badges**: Earned badges
- **caregiver_links**: Caregiver access permissions
- **nutrition_guidelines**: RAG knowledge base
- **offline_sync**: Sync status tracking

## 🔐 Security Features

### Authentication
- JWT-based authentication
- Password hashing with bcrypt
- Token expiration and refresh
- Role-based access control

### Authorization
- Premium feature gating
- Child ownership verification
- Caregiver permission management
- API rate limiting (configurable)

### Data Protection
- Row Level Security (RLS) in PostgreSQL
- Input validation with Pydantic
- SQL injection prevention
- Sensitive data encryption

## 🚀 Deployment

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=1000

# Pinecone (Optional)
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=tinytummy-guidelines

# Redis (Optional)
REDIS_URL=redis://localhost:6379

# Development
DEBUG=True
ENVIRONMENT=development
DISABLE_PREMIUM_CHECKS=False
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
```bash
# Using Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Docker
docker build -t tinytummy-backend .
docker run -p 8000:8000 tinytummy-backend
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
./scripts/test_all.sh

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Coverage
- **Authentication**: Registration, login, token validation
- **Meal Service**: GPT analysis, nutrition calculation
- **Integration**: End-to-end user flows
- **Premium Features**: Access control testing
- **Error Handling**: Invalid inputs and edge cases

## 🔄 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Children
- `POST /children` - Create child profile
- `GET /children` - List user's children
- `PUT /children/{id}` - Update child profile
- `DELETE /children/{id}` - Delete child profile

### Meals
- `POST /meals/log` - Log a meal with GPT analysis
- `GET /meals/{child_id}` - Get meals for child
- `GET /meals/trends/{child_id}` - Get nutrition trends

### Premium Features
- `POST /chat/query` - AI nutrition assistant
- `POST /plans/generate` - Generate meal plan
- `POST /reports/generate` - Generate nutrition report
- `POST /caregiver/invite` - Invite caregiver

### Gamification
- `GET /gamification/{child_id}` - Get user progress
- `GET /gamification/badges` - Get earned badges
- `GET /gamification/leaderboard` - Get leaderboard

### Sync
- `POST /sync/offline` - Sync offline data
- `GET /sync/server-data` - Get server data for sync

## 🎯 Performance Considerations

### Database Optimization
- Connection pooling with SQLAlchemy
- Indexed queries for meal trends
- Efficient RAG queries with Pinecone

### Caching Strategy
- Redis for session storage (optional)
- In-memory caching for frequently accessed data
- CDN for static assets

### Scalability
- Horizontal scaling with load balancers
- Database read replicas
- Microservice architecture ready

## 🔧 Development Notes

### Code Quality
- Type hints throughout
- Comprehensive error handling
- Centralized configuration
- Modular architecture

### Monitoring
- Structured logging
- Health check endpoints
- Performance metrics
- Error tracking

### Future Enhancements
- Real-time notifications
- Advanced analytics
- Mobile push notifications
- Multi-language support
- Advanced RAG with embeddings
- PDF generation service
- Payment integration
- Admin dashboard

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Check `DATABASE_URL` and network connectivity
2. **OpenAI API**: Verify API key and rate limits
3. **JWT Tokens**: Ensure secret key is set and tokens are valid
4. **Premium Features**: Check subscription tier and feature flags

### Debug Mode
Set `DEBUG=True` in environment for detailed error messages and SQL logging.

### Logs
Check application logs for detailed error information and request tracing. 