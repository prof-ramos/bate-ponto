# Implementation Plan

## Overview
Comprehensive plan to fix 5 critical issues in the Bate-Ponto Discord Bot project that affect performance, data integrity, and production readiness.

## Types
- **File Path Types**: String paths for all file operations with proper validation
- **User ID Types**:
  - **Decision**: user_id is stored as **str** in database.json for consistency
  - Discord.py API requires **int** for `fetch_member()` calls
  - Conversion is done in `fetch_user()` via `validate_and_convert_user_id()`
  - This approach maintains backward compatibility while enabling proper API usage
- **Lock Types**: File locking mechanisms for database operations
- **Configuration Types**: Separate production and development dependency configurations
- **Data Types**: Clean production data structures without test artifacts

## Files

### New Files to be Created
- `requirements-dev.txt` - Development dependencies (pytest, pytest-asyncio, pytest-cov)
- `database_lock.py` - File locking utilities for database operations

### Existing Files to be Modified
- `bot.py` - Fix dynamic imports and improve error handling
- `database.py` - Add file locking and atomic operations
- `requirements.txt` - Remove test dependencies
- `utils.py` - Add user ID conversion utilities
- `video_ranking.json` - Remove test data and initialize clean

### Files to be Deleted
- None

### Configuration File Updates
- `.gitignore` - Add lock files and temporary files
- `pytest.ini` - Update test configuration if needed

## Functions

### New Functions
- `database_lock.py`:
  - `acquire_file_lock(file_path: str) -> contextmanager` - Context manager for file locking
  - `atomic_write_json(data: dict, file_path: str) -> None` - Atomic JSON write with locking

### Modified Functions
- `bot.py`:
  - `create_bot()` - Remove dynamic imports, use static imports
  - `on_voice_state_update()` - Simplify error handling
  - `ranking_video_command()` - Simplify error handling

- `database.py`:
  - `save_data(data: dict) -> None` - Add file locking and atomic operations
  - `update_video_time(user_id: str, duration: int) -> None` - Add type conversion

- `utils.py`:
  - `safe_int_conversion(value: str) -> int` - Convert string to int with error handling
  - `validate_and_convert_user_id(user_id: str) -> int` - Validate and convert user ID

## Classes
- **New Classes**:
  - `FileLockManager` in `database_lock.py` - Manages file locking operations

- **Modified Classes**:
  - `VideoSessionManager` in `events.py` - No changes needed (already has asyncio.Lock)

## Dependencies
- **Production Dependencies** (requirements.txt):
  - discord.py>=2.3.0
  - python-dotenv>=1.0.0

- **Development Dependencies** (requirements-dev.txt):
  - pytest>=7.4.0
  - pytest-asyncio>=0.21.0
  - pytest-cov>=4.0.0

- **New Dependencies**:
  - portalocker>=2.0.0 (for cross-platform file locking)

## Testing
- **Test File Requirements**:
  - Add tests for file locking in `tests/test_database_lock.py`
  - Add tests for user ID conversion in `tests/test_utils.py`
  - Add integration tests for atomic operations

- **Existing Test Modifications**:
  - Update `tests/test_database.py` to test with file locking
  - Update `tests/test_events.py` to test with converted user IDs

- **Validation Strategies**:
  - Test concurrent database writes
  - Test user ID conversion edge cases
  - Test file locking under high concurrency

## Implementation Order
1. **Setup Phase**: Create requirements-dev.txt and database_lock.py
2. **Core Fixes**: Fix bot.py imports and database.py file locking
3. **Data Integrity**: Add user ID conversion and clean test data
4. **Validation**: Update tests and run comprehensive validation
5. **Cleanup**: Final verification and documentation updates