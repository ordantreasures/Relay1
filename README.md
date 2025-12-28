# Relay Backend

Campus discovery platform backend built with FastAPI.

## Features

- User authentication with JWT tokens
- Posts, comments, and communities
- Real-time notifications
- Search and filtering
- File upload support
- Gemini AI integration for content refinement

## Quick Start

### With Docker (Recommended)

1. Create `.env` file:
```bash
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=postgresql://postgres:password@db:5432/relay
REDIS_URL=redis://redis:6379/0