#!/bin/bash
set -e

echo "🚀 Starting AgentForge..."

# Run database schema creation via Python
python -c "
import asyncio
from backend.database import init_db
asyncio.run(init_db())
print('✅ Database initialized')
"

# Start the application
exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info
