# CLAUDE.md - Bate-Ponto Discord Bot

## Project Overview

Bate-Ponto is a Discord bot that gamifies video camera usage in voice channels. It tracks how long members keep their cameras on and maintains a leaderboard (top 10) ranking users by total camera-on time. Built with Python 3.10+ and discord.py 2.3+.

**Primary language:** Portuguese (BR) for user-facing text, docstrings, and documentation. Code identifiers (variables, functions) use English.

## Quick Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (requires .env with DISCORD_TOKEN)
python bot.py

# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_database.py -v

# Run integration tests
pytest tests/integration/ -v
```

## Architecture

### Module Structure (6-file modular design)

```
bot.py          → Entry point. Creates bot, registers events/commands, handles startup/shutdown.
config.py       → Environment variables, constants (EMBED_COLOR, MAX_RANKING_SIZE), intents setup, logger factory.
database.py     → JSON file persistence. load_data(), save_data(), update_video_time().
events.py       → VideoSessionManager (async-safe with asyncio.Lock), on_voice_state_update handler.
commands.py     → !rankingvideo command. Parallel user fetching with asyncio.gather().
utils.py        → format_seconds_to_time(), validate_user_id(), fetch_user(), truncate_string(), safe_int().
```

### Data Flow

1. User toggles camera in voice channel
2. `bot.py` receives `on_voice_state_update` event, delegates to `events.py`
3. `events.py` detects `self_video` change via `VideoSessionManager` (start/end session)
4. On camera off: calculates duration, calls `database.update_video_time()`
5. `database.py` loads JSON, updates user entry, saves back to `video_ranking.json`
6. When `!rankingvideo` is called: loads data, sorts by `total_seconds`, fetches members in parallel, builds Discord embed

### Data Storage

JSON file (`video_ranking.json`) in project root:
```json
{
  "user_id_string": {
    "total_seconds": 3600,
    "sessions": 5
  }
}
```

No ORM or external database. Planned migration to SQLite/PostgreSQL in Phase 3 (see `docs/ADRS.md` ADR-001).

## Key Conventions

### Code Style
- **Type hints** on all function signatures (project requirement RNF10)
- **Docstrings** on all functions with Args/Returns/Example sections
- PEP 8 style, ~100 char line length
- Imports ordered: stdlib, third-party (`discord`, `dotenv`), local modules
- No linter/formatter configured (no black, ruff, flake8)

### Async Patterns
- All Discord I/O uses `async/await`
- `VideoSessionManager` in `events.py` uses `asyncio.Lock()` for thread-safe session tracking
- `commands.py` uses `asyncio.gather()` for parallel member fetching (performance-critical)
- `bot.py` uses lazy imports inside event handlers to avoid circular imports

### Error Handling
- `database.py`: Corrupted JSON files are silently reset to empty `{}`
- `commands.py`: Missing/deleted Discord users are skipped silently (returns None from `fetch_user`)
- `bot.py`: `CommandNotFound` errors are ignored; other command errors send user-friendly messages
- Bot exits with `sys.exit(1)` on missing token or auth failure

### Naming
- Discord user IDs are always stored and passed as **strings** (not ints)
- Time durations are always in **seconds** (int)
- The single command is `!rankingvideo` (configurable prefix via `COMMAND_PREFIX` env var)

## Testing

### Framework & Config
- **pytest** with `pytest-asyncio` (auto mode) and `pytest-cov`
- Config in `pytest.ini`: test discovery in `tests/`, verbose output, coverage reporting
- Current coverage: ~82% overall (database.py: 97%, utils.py: 86%)

### Test Structure
```
tests/
├── conftest.py                  → Shared fixtures (mock_guild, mock_member, mock_voice_state, temp_data_file, sample_data)
├── test_database.py             → JSON persistence: load, save, update, corruption recovery
├── test_events.py               → Camera on/off detection, session management
├── test_events_concurrency.py   → asyncio.Lock race condition tests (10+ concurrent toggles)
├── test_utils.py                → Time formatting, ID validation, string utils
├── test_commands.py             → Ranking embed generation, parallel fetch, empty state
├── integration/
│   └── test_integration.py      → End-to-end bot startup and ranking flow
└── benchmark/
    └── performance_test.py      → Serial vs parallel fetch comparison
```

### Testing Patterns
- Discord objects are mocked using `unittest.mock.MagicMock` with `spec=discord.X`
- `temp_data_file` fixture swaps `database.DATA_FILE` to a temp file and restores after test
- Async tests use `pytest-asyncio` auto mode (no `@pytest.mark.asyncio` needed)
- `conftest.py` adds project root to `sys.path` for imports

## Environment

### Required
- `DISCORD_TOKEN` - Bot token from Discord Developer Portal (required, bot exits without it)
- `COMMAND_PREFIX` - Command prefix (default: `!`)

### Configuration Constants (config.py)
- `DATA_FILE` = `"video_ranking.json"`
- `EMBED_COLOR` = `0x5865F2` (Discord blue)
- `MAX_RANKING_SIZE` = `10`
- `TIME_FORMAT` = `"%Y-%m-%d %H:%M:%S"`

### Dependencies (requirements.txt)
- `discord.py>=2.3.0` - Discord API wrapper
- `python-dotenv>=1.0.0` - .env file loading
- `pytest>=7.4.0` - Test framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.0.0` - Coverage reporting

## Documentation

- `README.md` - User guide, installation, deployment (Portuguese)
- `PRD.md` - Full product requirements document with RF/RNF specs
- `docs/ARQUITETURA.md` - Architecture overview and dependency graph
- `docs/ARQUITETURA_VISAO_GERAL.md` - Detailed architecture deep dive
- `docs/ADRS.md` - 7 Architecture Decision Records (JSON choice, concurrency, parallelism, etc.)
- `docs/FASE1_RELATARIO.md` - Phase 1 implementation report

## Common Tasks for AI Assistants

### Adding a new command
1. Create the async handler function in `commands.py`
2. Register it in `bot.py` using `@bot.command(name='...')`
3. Use lazy import in `bot.py` handler to avoid circular imports
4. Add tests in `tests/test_commands.py`

### Modifying data schema
1. Update `database.py` functions (`load_data`, `save_data`, `update_video_time`)
2. Handle migration from old format in `load_data()` (backwards compatibility)
3. Update `tests/conftest.py` `sample_data` fixture
4. Update `tests/test_database.py`

### Adding event handlers
1. Create handler function in `events.py`
2. Register in `bot.py` `create_bot()` function
3. Use `VideoSessionManager` pattern if tracking state across events
4. Add concurrency tests if shared mutable state is involved
