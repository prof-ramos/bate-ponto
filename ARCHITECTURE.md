# Architecture Documentation - Bate-Ponto Discord Bot

## Overview

**Bate-Ponto** is a Discord bot that tracks and ranks users by their camera activity time in voice channels. The bot automatically detects when users turn their camera on/off, accumulates time per user, and provides a ranking command to display the top 10 most active users.

### Key Features

- **Automatic Camera Detection**: Listens to Discord voice state updates to detect camera toggles
- **Time Tracking**: Accumulates camera time per user with session counting
- **Ranking Display**: Shows top 10 users with formatted time display (hours, minutes, seconds)
- **Data Persistence**: JSON-based storage with file locking for concurrent access safety
- **Error Handling**: Graceful handling of deleted users and API errors

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.8+ |
| Discord API | discord.py >= 2.3.0 |
| Configuration | python-dotenv >= 1.0.0 |
| Data Storage | JSON (video_ranking.json) |
| File Locking | portalocker >= 3.2.0 |
| Testing | pytest >= 9.0.2 |

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Discord Infrastructure                       │
│  ┌──────────────┐          ┌──────────────┐      ┌──────────────┐ │
│  │   Voice      │          │   Text       │      │    Guild     │ │
│  │   Channels   │          │   Channels   │      │   Members    │ │
│  └──────┬───────┘          └──────┬───────┘      └──────┬───────┘ │
│         │                         │                      │         │
│         └─────────────────────────┴──────────────────────┘         │
│                                  │                                 │
│                         Discord Gateway API                         │
│                                  │                                 │
└──────────────────────────────────┼─────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Bot Application                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      bot.py (Entry Point)                     │  │
│  │  - Bot initialization                                         │  │
│  │  - Event routing                                              │  │
│  │  - Command registration                                       │  │
│  │  - Error handling                                             │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         ▼                    ▼                    ▼                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │   events.py  │   │  commands.py │   │  config.py   │            │
│  │              │   │              │   │              │            │
│  │ - Voice      │   │ - Ranking    │   │ - Token      │            │
│  │   State      │   │   Command    │   │ - Intents    │            │
│  │   Handler    │   │              │   │ - Logger     │            │
│  │ - Session    │   │              │   │              │            │
│  │   Manager    │   │              │   │              │            │
│  └──────┬───────┘   └──────┬───────┘   └──────────────┘            │
│         │                   │                                       │
│         └─────────┬─────────┘                                       │
│                   ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                       database.py                             │  │
│  │  - load_data()      - Load ranking from JSON                 │  │
│  │  - save_data()      - Save ranking to JSON                   │  │
│  │  - update_video_time() - Update user time atomically         │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   database_lock.py                            │  │
│  │  - acquire_file_lock()    - File locking with timeout        │  │
│  │  - atomic_write_json()    - Atomic write operations          │  │
│  │  - safe_load_json()       - Safe read with lock              │  │
│  │  - safe_update_json()     - Atomic read-modify-write         │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Persistence Layer                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              video_ranking.json (Atomic Operations)           │  │
│  │  {                                                           │  │
│  │    "123456789012345678": {                                   │  │
│  │      "total_seconds": 3600,                                  │  │
│  │      "sessions": 5                                           │  │
│  │    }                                                         │  │
│  │  }                                                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   User Request    │
                    │  !rankingvideo    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Discord Event    │
                    │  Voice State      │
                    │  Camera Toggle    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Response Embed  │
                    │  Top 10 Ranking  │
                    │  Formatted Time   │
                    └──────────────────┘
```

## Core Components

### 1. Entry Point (`bot.py`)

**Responsibilities:**
- Bot initialization and configuration
- Event handler registration
- Command registration
- Global error handling

**Key Functions:**
- `create_bot()`: Creates and configures the Discord bot instance
- `run_bot()`: Initializes and runs the bot with proper error handling

**Event Handlers:**
- `on_ready()`: Logs connection status and sets bot presence
- `on_voice_state_update()`: Delegates to `events.py` voice handler
- `on_command_error()`: Provides user-friendly error messages

### 2. Event Handler (`events.py`)

**Responsibilities:**
- Detect camera state changes via Discord voice events
- Manage active video sessions with concurrency protection
- Calculate session duration and trigger database updates

**Key Classes:**
- `VideoSessionManager`: Manages active video sessions with asyncio.Lock for thread safety
  - `start_session(user_id, timestamp)`: Start tracking a camera session
  - `end_session(user_id)`: End session and return duration
  - `has_session(user_id)`: Check if user has active session

**Key Functions:**
- `on_voice_state_update()`: Main event handler for voice state changes

### 3. Command Handler (`commands.py`)

**Responsibilities:**
- Implement user commands (currently `!rankingvideo`)
- Format and display ranking data as Discord embeds
- Handle parallel user lookups for performance

**Key Functions:**
- `ranking_video(ctx)`: Displays top 10 users by camera time
  - Uses `asyncio.gather()` for parallel member lookups
  - Formats time as hours/minutes/seconds
  - Creates styled Discord embed with server information

### 4. Database Layer (`database.py`)

**Responsibilities:**
- Load and save ranking data from/to JSON file
- Provide atomic update operations with file locking
- Handle file creation and error recovery

**Key Functions:**
- `load_data()`: Load ranking data, creates file if missing
- `save_data(data)`: Save data atomically with file locking
- `update_video_time(user_id, duration)`: Atomically update user time

**Data Format:**
```json
{
  "123456789012345678": {
    "total_seconds": 3600,
    "sessions": 5
  }
}
```

### 5. File Locking (`database_lock.py`)

**Responsibilities:**
- Provide cross-platform file locking mechanisms
- Implement atomic JSON operations
- Prevent TOCTOU (Time-of-Check to Time-of-Use) race conditions

**Key Functions:**
- `acquire_file_lock()`: Context manager for file locking with timeout
- `atomic_write_json()`: Write JSON atomically with temp file + rename
- `safe_load_json()`: Load JSON with read lock
- `safe_update_json()`: Atomic read-modify-write operation

**Locking Strategy:**
- Uses `portalocker` for cross-platform file locking
- Implements exponential backoff for retry logic
- Prevents concurrent write access to JSON data file

### 6. Utilities (`utils.py`)

**Responsibilities:**
- Time formatting and display
- User ID validation (Discord snowflake format: 18-19 digits)
- Safe type conversions
- Discord user fetching with error handling

**Key Functions:**
- `format_seconds_to_time()`: Convert seconds to readable format (Xh Ymin)
- `validate_user_id()`: Validate Discord snowflake ID format
- `validate_and_convert_user_id()`: Validate and convert string ID to int
- `fetch_user()`: Fetch Discord member with error handling
- `truncate_string()`: Truncate strings with suffix
- `setup_logger()`: Configure structured logging

### 7. Configuration (`config.py`)

**Responsibilities:**
- Load environment variables from `.env`
- Define project constants
- Configure Discord intents
- Setup logging

**Configuration Values:**
- `DISCORD_TOKEN`: Bot authentication token
- `COMMAND_PREFIX`: Command prefix (default: "!")
- `DATA_FILE`: Path to JSON data file
- `EMBED_COLOR`: Discord embed color (0x5865F2)
- `MAX_RANKING_SIZE`: Maximum ranking entries (10)

## Data Stores

### Primary Data Store: JSON File

**File:** `video_ranking.json`

**Schema:**
```json
{
  "<user_id_str>": {
    "total_seconds": <int>,
    "sessions": <int>
  }
}
```

**Example:**
```json
{
  "123456789012345678": {
    "total_seconds": 3665,
    "sessions": 5
  },
  "987654321098765432": {
    "total_seconds": 7200,
    "sessions": 3
  }
}
```

**Characteristics:**
- **Format:** JSON with 2-space indentation (RNF12)
- **Encoding:** UTF-8
- **Concurrency:** Protected by file locking (portalocker)
- **Atomicity:** Uses temp file + os.replace() for atomic writes
- **Recovery:** Auto-creates empty file if missing

### In-Memory Store: Active Sessions

**Location:** `events.py` - `VideoSessionManager`

**Schema:**
```python
{
  "<user_id_str>": <datetime_object>
}
```

**Characteristics:**
- **Type:** Dictionary with asyncio.Lock protection
- **Purpose:** Track active camera sessions
- **Lifetime:** In-memory only (lost on restart)
- **Recovery:** Sessions auto-end on bot restart (data loss acceptable)

## External Integrations

### Discord API

**Library:** discord.py >= 2.3.0

**Intents Required:**
- `guilds`: Basic server operations
- `voice_states`: Detect camera state changes
- `members`: Fetch user information for ranking

**Events Used:**
- `on_voice_state_update`: Primary event for camera detection
- `on_ready`: Connection status
- `on_command_error`: Command error handling

**API Operations:**
- `guild.fetch_member(id)`: Fetch member by ID
- `ctx.send()`: Send messages/embeds
- `bot.change_presence()`: Set bot status

**Error Handling:**
- `discord.NotFound`: User deleted/not found
- `discord.HTTPException`: API errors
- `discord.LoginFailure`: Authentication failure
- `discord.ConnectionClosed`: Connection loss

### Environment Variables

**Required:**
- `DISCORD_TOKEN`: Bot authentication token

**Optional:**
- `COMMAND_PREFIX`: Command prefix (default: "!")

## Deployment & Infrastructure

### Deployment Model

**Type:** Single-instance bot application

**Hosting Options:**
- Local development machine
- VPS (e.g., DigitalOcean, AWS EC2)
- Containerized (Docker)
- Serverless (not recommended due to persistent connections)

### System Requirements

**Minimum:**
- Python 3.8+
- 512MB RAM
- Stable internet connection
- Disk space for JSON file (<1MB typical)

**Recommended:**
- Python 3.10+
- 1GB RAM
- 99.9% uptime connectivity
- Backup for JSON file

### Deployment Steps

1. **Environment Setup:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

2. **Configuration:**
```bash
cp .env.example .env
# Edit .env with DISCORD_TOKEN
```

3. **Running:**
```bash
python bot.py
```

4. **Production Considerations:**
- Use process manager (systemd, supervisor, PM2)
- Configure log rotation
- Set up JSON file backups
- Monitor for restarts

### Process Management (systemd example)

```ini
[Unit]
Description=Bate-Ponto Discord Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/bate-ponto
Environment="PATH=/opt/bate-ponto/venv/bin"
ExecStart=/opt/bate-ponto/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Security Considerations

### Authentication & Authorization

**Discord Token Security:**
- Token stored in `.env` file (not in code)
- `.env` excluded from version control via `.gitignore`
- Token should be bot token (not user token)
- Minimum required intents only

### Data Protection

**User Data:**
- Only stores Discord user IDs (snowflakes)
- No personal information stored
- User IDs are public Discord identifiers
- Data visible to anyone with file access

**File Permissions:**
- JSON file should have restricted permissions (600 or 640)
- `.env` file should have restricted permissions (600)

### Input Validation

**User ID Validation:**
- Regex validation for 18-19 digit numeric strings
- Type checking for all function parameters
- Safe conversion with error handling

**Duration Validation:**
- Negative durations rejected
- Integer type required
- Maximum practical limits enforced

### Concurrency Safety

**Race Condition Prevention:**
- File locking for all JSON operations
- asyncio.Lock for session management
- Atomic read-modify-write operations
- TOCTOU prevention in database operations

### Error Handling

**Graceful Degradation:**
- Deleted users handled silently (return None)
- API errors logged but don't crash bot
- File lock timeouts with exponential backoff
- Corrupted JSON recovers to empty state

## Development Environment

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)
- Discord Bot Token

### Project Structure

```
bate-ponto/
├── bot.py                 # Entry point
├── config.py              # Configuration
├── database.py            # Data persistence
├── database_lock.py       # File locking
├── events.py              # Event handlers
├── commands.py            # Bot commands
├── utils.py               # Utility functions
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pytest.ini             # Pytest configuration
├── .gitignore            # Git ignore rules
├── .env.example          # Environment template
├── video_ranking.json    # Data file (auto-created)
├── ARCHITECTURE.md       # This file
├── implementation_plan.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # Test fixtures
│   ├── test_database.py  # Database tests
│   ├── test_utils.py     # Utility tests
│   └── test_events.py    # Event handler tests
└── .claude/
    └── ...               # Claude Code configuration
```

### Development Workflow

1. **Setup:**
```bash
git clone <repo>
cd bate-ponto
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2. **Testing:**
```bash
pytest                    # Run all tests
pytest -v                # Verbose output
pytest -x               # Stop on first failure
pytest tests/test_database.py  # Specific file
```

3. **Code Style:**
- Follow PEP 8 guidelines
- Use type hints (RNF10)
- Docstrings for all public functions
- UTF-8 encoding for all files

### Dependencies

**Production (`requirements.txt`):**
```
discord.py>=2.3.0        # Discord API wrapper
python-dotenv>=1.0.0     # Environment variable loading
```

**Development (`requirements-dev.txt`):**
```
pytest>=9.0.2            # Testing framework
pytest-asyncio>=1.3.0    # Async test support
pytest-cov>=7.0.0        # Coverage reporting
portalocker>=3.2.0       # File locking (also needed in production)
```

## Configuration Management

### Environment Variables

**Required:**
```bash
DISCORD_TOKEN=<bot_token_here>
```

**Optional:**
```bash
COMMAND_PREFIX=!          # Default: "!"
```

### Configuration File (`.env`)

**Example (`.env.example`):**
```bash
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token_here

# Optional: Command prefix (default: !)
# COMMAND_PREFIX=!
```

### Application Constants

**Defined in `config.py`:**

```python
# File paths
DATA_FILE = "video_ranking.json"

# Discord embed settings
EMBED_COLOR = 0x5865F2    # Discord blurple
MAX_RANKING_SIZE = 10

# Logging
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
```

### Discord Intents

**Configuration:**
```python
intents = discord.Intents.default()
intents.guilds = True       # Server operations
intents.voice_states = True # Camera detection
intents.members = True      # User lookup
```

**Note:** `members` intent requires enabling in Discord Developer Portal.

## Monitoring & Observability

### Logging

**Logger Configuration:**
- **Format:** `timestamp - name - level - message`
- **Level:** INFO (configurable)
- **Output:** Console (file optional)

**Key Log Events:**
- Bot connection status
- Camera toggle events
- Database operations
- Error conditions

**Example:**
```
2026-02-19 10:30:15 - bate-ponto - INFO - Bot conectado como BotName#1234
2026-02-19 10:30:15 - bate-ponto - INFO - ID do bot: 987654321098765432
2026-02-19 10:30:15 - bate-ponto - INFO - Conectado a 1 servidores
2026-02-19 10:31:22 - events - INFO - 📹 João ligou a câmera
2026-02-19 10:35:10 - events - INFO - 📹 João desligou - 228s gravados
```

### Health Monitoring

**Manual Checks:**
- Bot presence status (should show "watching câmeras ligadas")
- Response to `!rankingvideo` command
- JSON file size and validity

**Recommended Metrics:**
- Bot uptime
- Camera toggle events per hour
- Command success rate
- Response latency

### Error Tracking

**Error Categories:**
1. **Discord API Errors:** HTTP exceptions, connection issues
2. **Database Errors:** File lock timeouts, JSON corruption
3. **Validation Errors:** Invalid user IDs, negative durations

**Error Handling Strategy:**
- Log all errors with stack trace
- User-friendly messages for command errors
- Silent handling for deleted users
- Graceful degradation where possible

## Testing Strategy

### Test Structure

**Test Files:**
- `tests/test_database.py`: Database operations
- `tests/test_utils.py`: Utility functions
- `tests/test_events.py`: Event handlers

### Test Categories

#### Unit Tests

**Database Tests (`test_database.py`):**
- `load_data()` - File creation, empty file, valid data, corrupted JSON
- `save_data()` - JSON validity, indentation, Unicode support
- `update_video_time()` - New users, existing users, negative duration, concurrent updates

**Utility Tests (`test_utils.py`):**
- `format_seconds_to_time()` - Seconds, minutes, hours, invalid input
- `validate_user_id()` - Valid IDs (18-19 digits), invalid length/characters
- `validate_seconds()` - Valid/invalid seconds
- `safe_int()` - Valid conversion, invalid with default
- `validate_and_convert_user_id()` - Valid format, invalid format, type errors
- `truncate_string()` - Within limit, exceeds limit, custom suffix
- `setup_logger()` - Basic, custom level, with file

**Event Tests (`test_events.py`):**
- Camera on/off detection
- Session duration calculation
- Database update triggering

#### Integration Tests

**Concurrent Updates (`test_database.py`):**
```python
def test_concurrent_updates_with_locking():
    # Tests multiple threads updating simultaneously
    # Verifies file locking prevents data corruption
```

### Test Fixtures (`conftest.py`)

**Fixtures:**
- `temp_data_file`: Temporary JSON file for isolated testing
- `sample_data`: Pre-populated test data
- `bot`: Test bot instance
- `guild`: Mock Discord guild

### Running Tests

**Basic:**
```bash
pytest
```

**Verbose:**
```bash
pytest -v
```

**Coverage:**
```bash
pytest --cov=. --cov-report=html
```

**Specific Test:**
```bash
pytest tests/test_utils.py::TestFormatSecondsToTime
```

### Test Coverage

**Current Coverage:** 63 tests passing

**Coverage Areas:**
- ✅ All database operations
- ✅ All utility functions
- ✅ File locking mechanisms
- ✅ Concurrent access patterns
- ⚠️ Event handlers (limited due to Discord.py complexity)

### Test Data Management

**Isolation Strategy:**
- Temporary files for each test
- Fresh database state per test
- Mock Discord objects where needed

**Sample Data:**
```python
{
    "123456789012345678": {
        "total_seconds": 3600,
        "sessions": 5
    }
}
```

---

## Appendix

### Type Conventions

- **user_id**: Stored as `str` in JSON, converted to `int` for Discord API
- **duration**: `int` (non-negative seconds)
- **timestamps**: `datetime.datetime` objects
- **sessions**: `int` (count)

### Error Reference

| Error | Cause | Handling |
|-------|-------|----------|
| `FileLockError` | File lock timeout | Exponential backoff, retry |
| `ValueError` | Invalid input format | User-friendly message |
| `discord.NotFound` | User deleted | Silent skip (return None) |
| `discord.HTTPException` | API error | Log and continue |

### References

- **Discord.py Documentation:** https://discordpy.readthedocs.io/
- **Discord API Documentation:** https://discord.com/developers/docs/intro
- **portalocker:** https://github.com/WoLpH/portalocker
