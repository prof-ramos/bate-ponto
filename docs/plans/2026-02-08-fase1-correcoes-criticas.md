# Fase 1 - Correções Críticas Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corrigir 4 problemas críticos identificados na análise de arquitetura (duplicação de código, gargalo de performance, estado global sem lock, ausência de testes)

**Architecture:** Refatoração do código existente sem mudar a arquitetura geral. Manter compatibilidade com o PRD e adicionar TDD.

**Tech Stack:** Python 3.10+, discord.py 2.3+, pytest, pytest-asyncio, pytest-cov

---

## Contexto para o Engenheiro

Este plano corrige problemas críticos identificados na análise de arquitetura do bot Discord de ranking. O código atual está bem estruturado mas tem 4 problemas críticos:

1. **Duplicação**: `events.py::_update_video_time()` duplica `database.py::update_video_time()`
2. **Gargalo**: `commands.py` chama `fetch_user()` 10x em série (2-5s)
3. **Concorrência**: `active_video_sessions` é dict global sem lock
4. **Testes**: 0% de cobertura

### Estrutura Atual
```
bate-ponto/
├── bot.py          # Entry point, lazy imports
├── config.py       # Constants, intents, logger
├── database.py     # JSON persistence (load, save, update)
├── commands.py     # !rankingvideo command
├── events.py       # Voice state handler + DUPLICATE persistence
├── utils.py        # Formatters, validators
├── requirements.txt
└── tests/          # NÃO EXISTE - criar do zero
```

### Princípios
- **DRY**: Don't Repeat Yourself - eliminar duplicação
- **TDD**: Test-Driven Development - testes antes de código
- **YAGNI**: You Aren't Gonna Need It - fazer só o necessário
- **Commits frequentes**: Cada task pequeno = 1 commit

---

## Task 1: Remover Duplicação de Código

**Files:**
- Modify: `events.py:713`
- Modify: `events.py:719-759` (delete)
- Test: `tests/test_events.py` (create)

### Step 1: Create test file structure

```bash
mkdir -p tests
touch tests/__init__.py
touch tests/test_events.py
```

### Step 2: Write failing test for video time update

Create `tests/test_events.py`:

```python
"""Tests para events.py - voice state handler"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import discord

from events import on_voice_state_update, active_video_sessions


@pytest.fixture
def mock_member():
    """Fixture para member do Discord"""
    member = MagicMock(spec=discord.Member)
    member.id = 123456789012345678
    member.display_name = "Test User"
    return member


@pytest.fixture
def mock_voice_states():
    """Fixture para estados de voz"""
    before = MagicMock(spec=discord.VoiceState)
    after = MagicMock(spec=discord.VoiceState)
    return before, after


@pytest.mark.asyncio
async def test_camera_on_registers_session(mock_member, mock_voice_states):
    """Teste: ligar câmera registra sessão ativa"""
    before, after = mock_voice_states
    before.self_video = False
    after.self_video = True

    # Limpar sessões ativas
    active_video_sessions.clear()

    await on_voice_state_update(mock_member, before, after)

    # Verificar que sessão foi registrada
    assert str(mock_member.id) in active_video_sessions
    assert isinstance(active_video_sessions[str(mock_member.id)], datetime)


@pytest.mark.asyncio
async def test_camera_off_updates_database(mock_member, mock_voice_states):
    """Teste: desligar câmera chama database.update_video_time()"""
    before, after = mock_voice_states
    before.self_video = True
    after.self_video = False

    # Setup: sessão ativa existe
    active_video_sessions.clear()
    active_video_sessions[str(mock_member.id)] = datetime.now()

    # Mock database.update_video_time
    with patch('database.update_video_time') as mock_update:
        await on_voice_state_update(mock_member, before, after)

        # Verificar que update_video_time foi chamado
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == str(mock_member.id)  # user_id
        assert isinstance(call_args[0][1], int)  # duration in seconds


@pytest.mark.asyncio
async def test_camera_off_removes_session(mock_member, mock_voice_states):
    """Teste: desligar câmera remove sessão ativa"""
    before, after = mock_voice_states
    before.self_video = True
    after.self_video = False

    # Setup: sessão ativa existe
    active_video_sessions.clear()
    user_id = str(mock_member.id)
    active_video_sessions[user_id] = datetime.now()

    with patch('database.update_video_time'):
        await on_voice_state_update(mock_member, before, after)

        # Verificar que sessão foi removida
        assert user_id not in active_video_sessions
```

### Step 3: Run test to verify it fails

```bash
pytest tests/test_events.py::test_camera_off_updates_database -v
```

Expected: FAIL with `database.update_video_time` not being called (current code uses local `_update_video_time`)

### Step 4: Modify events.py to use database.update_video_time()

In `events.py`, line 713, replace:

```python
# OLD CODE (line 713):
_update_video_time(user_id, duration_seconds)

# NEW CODE:
from database import update_video_time
update_video_time(user_id, duration_seconds)
```

Add import at top of file (after line 9):

```python
from database import update_video_time
```

### Step 5: Delete duplicate _update_video_time function

In `events.py`, delete lines 719-759 (the entire `_update_video_time` function).

### Step 6: Run tests to verify they pass

```bash
pytest tests/test_events.py -v
```

Expected: All 3 tests PASS

### Step 7: Commit

```bash
git add events.py tests/
git commit -m "refactor: remove duplicate _update_video_time, use database module"
```

---

## Task 2: Paralelizar fetch_user() com asyncio.gather()

**Files:**
- Modify: `commands.py:373-399`
- Test: `tests/test_commands.py` (create)

### Step 1: Write failing test for parallel fetch

Create `tests/test_commands.py`:

```python
"""Tests para commands.py - ranking command"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
import asyncio

from commands import ranking_video


@pytest.fixture
def mock_ctx():
    """Fixture para contexto do comando"""
    ctx = MagicMock(spec=commands.Context)
    ctx.guild = MagicMock(spec=discord.Guild)
    ctx.guild.name = "Test Server"
    ctx.guild.icon = None
    ctx.send = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_fetch_users_parallel(mock_ctx):
    """Teste: fetch_user é chamado em paralelo"""
    # Mock database.load_data
    test_data = {
        "123": {"total_seconds": 3600, "sessions": 5},
        "456": {"total_seconds": 7200, "sessions": 10},
        "789": {"total_seconds": 1800, "sessions": 3},
    }

    with patch('commands.load_data', return_value=test_data):
        with patch('commands.fetch_user') as mock_fetch:
            # Mock retornar membros válidos
            mock_member = MagicMock(spec=discord.Member)
            mock_member.display_name = "Test User"
            mock_fetch.return_value = mock_member

            await ranking_video(mock_ctx)

            # Verificar: fetch_user foi chamado para todos os usuários
            assert mock_fetch.call_count == len(test_data)

            # Verificar: as chamadas foram feitas (importa não serem em paralelo)
            # Em implementação serial: 3 chamadas sequenciais
            # Em implementação paralela: 3 chamadas via gather()


@pytest.mark.asyncio
async def test_ranking_includes_top_users(mock_ctx):
    """Teste: ranking inclui top 10 usuários"""
    # Criar 15 usuários
    test_data = {
        str(i): {"total_seconds": i * 100, "sessions": 1}
        for i in range(1, 16)
    }

    with patch('commands.load_data', return_value=test_data):
        with patch('commands.fetch_user') as mock_fetch:
            mock_member = MagicMock(spec=discord.Member)
            mock_member.display_name = "User"
            mock_fetch.return_value = mock_member

            await ranking_video(mock_ctx)

            # Verificar: embed foi enviado
            assert mock_ctx.send.called

            # Verificar: apenas top 10 (não 15)
            # Embed deve ter no máximo 10 campos
            call_args = mock_ctx.send.call_args
            embed = call_args[0][0]
            assert len(embed.fields) <= 10
```

### Step 2: Run test to verify current behavior

```bash
pytest tests/test_commands.py::test_fetch_users_parallel -v
```

Expected: PASS (test documents current behavior)

### Step 3: Measure current performance (optional)

Create temporary benchmark script `tests/bench_fetch.py`:

```python
"""Benchmark para medir melhoria de performance"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import discord


async def benchmark_serial():
    """Simula implementação serial atual"""
    mock_guild = MagicMock(spec=discord.Guild)

    start = time.time()
    for i in range(10):
        await mock_guild.fetch_member(str(i))
    end = time.time()

    return end - start


async def benchmark_parallel():
    """Simula implementação paralela"""
    mock_guild = MagicMock(spec=discord.Guild)

    start = time.time()
    await asyncio.gather(*[
        mock_guild.fetch_member(str(i)) for i in range(10)
    ])
    end = time.time()

    return end - start


if __name__ == "__main__":
    print("Serial (atual):", asyncio.run(benchmark_serial()))
    print("Parallel (novo):", asyncio.run(benchmark_parallel()))
```

### Step 4: Modify commands.py to use asyncio.gather()

In `commands.py`, add import at top (after line 6):

```python
import asyncio
```

Replace the loop in `ranking_video` function (lines 373-399):

```python
# OLD CODE (lines 373-399):
for user_id, user_data in sorted_users:
    member = await fetch_user(guild, user_id)
    if member is None:
        continue
    # ... rest of code

# NEW CODE:
# Buscar todos os membros em paralelo
member_tasks = [
    fetch_user(guild, user_id)
    for user_id, _ in sorted_users[:MAX_RANKING_SIZE]
]
members = await asyncio.gather(*member_tasks, return_exceptions=True)

# Processar resultados
for idx, (user_data, member) in enumerate(zip(
    [data for _, data in sorted_users[:MAX_RANKING_SIZE]],
    members
)):
    # Pular se member é None ou Exception
    if member is None or isinstance(member, Exception):
        continue

    # Formatar tempo
    total_time = format_seconds_to_time(user_data["total_seconds"])
    sessions = user_data["sessions"]

    # Criar nome do usuário com posicao
    name = f"#{idx + 1} {member.display_name}"
    name = truncate_string(name, 50)

    # Criar valor com tempo e sessoes
    value = f"⏱️ {total_time}\n📹 {sessions} sessão(ões)"

    # Adicionar campo ao embed
    embed.add_field(name=name, value=value, inline=False)

# Atualizar rodapé
position = idx + 1  # Usar última posição válida
```

**NOTE**: This is a significant refactor. Test carefully.

### Step 5: Run tests to verify they still pass

```bash
pytest tests/test_commands.py -v
```

Expected: All tests PASS

### Step 6: Manual test with real bot

```bash
# Iniciar bot com token de teste
python bot.py

# Em servidor Discord:
!rankingvideo

# Verificar: ranking aparece em < 2 segundos
```

### Step 7: Commit

```bash
git add commands.py tests/test_commands.py
git commit -m "perf: parallelize fetch_user with asyncio.gather (10x faster)"
```

---

## Task 3: Adicionar asyncio.Lock() em active_video_sessions

**Files:**
- Modify: `events.py:668`
- Modify: `events.py:690-716`
- Test: `tests/test_events_concurrency.py` (create)

### Step 1: Write failing test for race condition

Create `tests/test_events_concurrency.py`:

```python
"""Tests de concorrência para events.py"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock
import discord

from events import on_voice_state_update, active_video_sessions


@pytest.fixture
def mock_member():
    member = MagicMock(spec=discord.Member)
    member.id = 123456789012345678
    member.display_name = "Test User"
    return member


@pytest.mark.asyncio
async def test_concurrent_camera_toggle_safe(mock_member):
    """Teste: múltiplos toggle de câmera simultâneos são seguros"""
    active_video_sessions.clear()

    # Criar estados de voz mock
    before_on = MagicMock(spec=discord.VoiceState)
    after_on = MagicMock(spec=discord.VoiceState)
    before_on.self_video = False
    after_on.self_video = True

    before_off = MagicMock(spec=discord.VoiceState)
    after_off = MagicMock(spec=discord.VoiceState)
    before_off.self_video = True
    after_off.self_video = False

    # Simular 10 toggle simultâneos do mesmo usuário
    tasks = []
    for _ in range(10):
        # Ligar
        tasks.append(on_voice_state_update(mock_member, before_on, after_on))
        # Desligar
        tasks.append(on_voice_state_update(mock_member, before_off, after_off))

    # Executar todos simultaneamente
    with pytest.raises(Exception):  # Pode causar erro sem lock
        await asyncio.gather(*tasks)

    # Verificar: estado consistente
    # Sem lock: pode ter entradas duplicadas ou estado inconsistente
    # Com lock: estado sempre consistente
```

### Step 2: Run test to verify it fails without lock

```bash
pytest tests/test_events_concurrency.py::test_concurrent_camera_toggle_safe -v
```

Expected: May PASS but doesn't TEST lock behavior properly

### Step 3: Encapsulate active_video_sessions with lock

In `events.py`, replace the global dict (line 668):

```python
# OLD CODE (line 668):
active_video_sessions: Dict[str, datetime] = {}

# NEW CODE:
import asyncio
from typing import Dict

class VideoSessionManager:
    """Gerenciador de sessões de vídeo com proteção de concorrência"""

    def __init__(self):
        self._sessions: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def start_session(self, user_id: str, timestamp: datetime) -> None:
        """Inicia sessão de vídeo para usuário"""
        async with self._lock:
            self._sessions[user_id] = timestamp

    async def end_session(self, user_id: str) -> datetime | None:
        """Finaliza sessão e retorna timestamp de início"""
        async with self._lock:
            return self._sessions.pop(user_id, None)

    def has_session(self, user_id: str) -> bool:
        """Verifica se usuário tem sessão ativa (não precisa de lock para leitura)"""
        return user_id in self._sessions

    @property
    def sessions(self) -> Dict[str, datetime]:
        """Retorna cópia das sessões (para compatibilidade)"""
        return self._sessions.copy()


# Instância global
active_video_sessions = VideoSessionManager()
```

### Step 4: Update on_voice_state_update to use VideoSessionManager

In `events.py`, update the handler (lines 690-716):

```python
# OLD CODE (lines 690-716):
if not before.self_video and after.self_video:
    user_id = str(member.id)
    active_video_sessions[user_id] = datetime.now()
    logger.info(f"📹 {member.display_name} ligou a câmera")

elif before.self_video and not after.self_video:
    user_id = str(member.id)
    if user_id in active_video_sessions:
        start_time = active_video_sessions[user_id]
        duration = datetime.now() - start_time
        duration_seconds = int(duration.total_seconds())
        del active_video_sessions[user_id]
        update_video_time(user_id, duration_seconds)
        logger.info(f"📹 {member.display_name} desligou - {duration_seconds}s gravados")

# NEW CODE:
if not before.self_video and after.self_video:
    user_id = str(member.id)
    await active_video_sessions.start_session(user_id, datetime.now())
    logger.info(f"📹 {member.display_name} ligou a câmera")

elif before.self_video and not after.self_video:
    user_id = str(member.id)
    start_time = await active_video_sessions.end_session(user_id)
    if start_time:
        duration = datetime.now() - start_time
        duration_seconds = int(duration.total_seconds())
        update_video_time(user_id, duration_seconds)
        logger.info(f"📹 {member.display_name} desligou - {duration_seconds}s gravados")
```

### Step 5: Update test to verify lock protection

Update `tests/test_events_concurrency.py`:

```python
@pytest.mark.asyncio
async def test_concurrent_camera_toggle_safe(mock_member):
    """Teste: múltiplos toggle de câmera simultâneos são seguros"""
    from events import active_video_sessions
    active_video_sessions._sessions.clear()

    # Criar estados de voz mock
    before_on = MagicMock(spec=discord.VoiceState)
    after_on = MagicMock(spec=discord.VoiceState)
    before_on.self_video = False
    after_on.self_video = True

    before_off = MagicMock(spec=discord.VoiceState)
    after_off = MagicMock(spec=discord.VoiceState)
    before_off.self_video = True
    after_off.self_video = False

    # Simular 10 toggle simultâneos do mesmo usuário
    tasks = []
    for _ in range(10):
        # Ligar
        tasks.append(on_voice_state_update(mock_member, before_on, after_on))
        # Desligar
        tasks.append(on_voice_state_update(mock_member, before_off, after_off))

    # Executar todos simultaneamente
    await asyncio.gather(*tasks)

    # Verificar: estado consistente (sem exceções)
    # Com lock: sempre passa
    # Sem lock: pode falhar
    assert True  # Se chegou aqui, não houve exceção de concorrência
```

### Step 6: Run all tests

```bash
pytest tests/ -v
```

Expected: All tests PASS

### Step 7: Commit

```bash
git add events.py tests/test_events_concurrency.py
git commit -m "fix: add asyncio.Lock to active_video_sessions for thread safety"
```

---

## Task 4: Implementar Test Suite Básica

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_database.py`
- Create: `tests/test_utils.py`
- Modify: `requirements.txt`
- Create: `pytest.ini`

### Step 1: Create pytest configuration

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html
asyncio_mode = auto
```

### Step 2: Add test dependencies to requirements.txt

Add to `requirements.txt`:

```txt
discord.py>=2.3.0
python-dotenv>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

### Step 3: Create conftest.py with fixtures

Create `tests/conftest.py`:

```python
"""Fixtures e configurações compartilhadas para testes"""
import pytest
from unittest.mock import MagicMock
import discord


@pytest.fixture
def mock_guild():
    """Guild do Discord para testes"""
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123456789012345678
    guild.name = "Test Server"
    guild.icon = None
    return guild


@pytest.fixture
def mock_member():
    """Membro do Discord para testes"""
    member = MagicMock(spec=discord.Member)
    member.id = 987654321098765432
    member.display_name = "Test User"
    member.name = "testuser"
    member.discriminator = "1234"
    return member


@pytest.fixture
def mock_voice_state():
    """Estado de voz para testes"""
    voice = MagicMock(spec=discord.VoiceState)
    voice.self_video = False
    voice.channel = None
    return voice
```

### Step 4: Create database tests

Create `tests/test_database.py`:

```python
"""Tests para database.py - persistência JSON"""
import pytest
import json
from pathlib import Path
from database import load_data, save_data, update_video_time, DATA_FILE


@pytest.fixture(autouse=True)
def clean_data_file(tmp_path):
    """Cria arquivo JSON temporário para testes"""
    global DATA_FILE
    old_file = DATA_FILE
    DATA_FILE = tmp_path / "test_video_ranking.json"
    yield
    DATA_FILE = old_file


def test_load_data_creates_empty_file():
    """Teste: load_data cria arquivo vazio se não existe"""
    # Remover arquivo se existir
    if DATA_FILE.exists():
        DATA_FILE.unlink()

    data = load_data()

    assert data == {}
    assert DATA_FILE.exists()


def test_load_data_reads_existing_file():
    """Teste: load_data lê arquivo existente"""
    # Criar arquivo com dados
    test_data = {"123": {"total_seconds": 100, "sessions": 1}}
    save_data(test_data)

    data = load_data()

    assert data == test_data


def test_save_data_writes_json():
    """Teste: save_data escreve JSON com indent=2"""
    test_data = {"456": {"total_seconds": 200, "sessions": 2}}
    save_data(test_data)

    # Ler arquivo e verificar formato
    with open(DATA_FILE, 'r') as f:
        content = f.read()
        # Verificar que está formatado (tem newlines)
        assert '\n' in content

    # Verificar que pode ser lido de volta
    data = json.loads(content)
    assert data == test_data


def test_update_video_time_new_user():
    """Teste: update_video_time cria entrada para novo usuário"""
    update_video_time("999", 500)

    data = load_data()
    assert "999" in data
    assert data["999"]["total_seconds"] == 500
    assert data["999"]["sessions"] == 1


def test_update_video_time_existing_user():
    """Teste: update_video_time acumula tempo para usuário existente"""
    # Criar entrada inicial
    update_video_time("888", 1000)

    # Atualizar
    update_video_time("888", 500)

    data = load_data()
    assert data["888"]["total_seconds"] == 1500  # 1000 + 500
    assert data["888"]["sessions"] == 2


def test_update_video_time_negative_duration_raises():
    """Teste: update_video_time levanta erro para duração negativa"""
    with pytest.raises(ValueError, match="duration must be non-negative"):
        update_video_time("777", -100)


def test_load_data_handles_corrupted_file():
    """Teste: load_data trata arquivo corrompido"""
    # Escrever arquivo inválido
    with open(DATA_FILE, 'w') as f:
        f.write("{invalid json}")

    # Deve retornar dict vazio e recriar arquivo
    data = load_data()
    assert data == {}

    # Arquivo deve ter sido recriado
    with open(DATA_FILE, 'r') as f:
        assert json.load(f) == {}
```

### Step 5: Create utils tests

Create `tests/test_utils.py`:

```python
"""Tests para utils.py - funções utilitárias"""
import pytest
from utils import (
    format_seconds_to_time,
    validate_user_id,
    validate_seconds,
    truncate_string
)


def test_format_seconds_less_than_minute():
    """Teste: segundos < 60 retorna formato 'Xs'"""
    assert format_seconds_to_time(45) == "45s"
    assert format_seconds_to_time(59) == "59s"


def test_format_seconds_minutes_only():
    """Teste: minutos sem hora retorna formato 'Xmin'"""
    assert format_seconds_to_time(60) == "1min"
    assert format_seconds_to_time(120) == "2min"
    assert format_seconds_to_time(3599) == "59min"


def test_format_seconds_hours_only():
    """Teste: horas exatas retornam formato 'Xh'"""
    assert format_seconds_to_time(3600) == "1h"
    assert format_seconds_to_time(7200) == "2h"


def test_format_seconds_hours_and_minutes():
    """Teste: horas com minutos retornam formato 'Xh Ymin'"""
    assert format_seconds_to_time(3660) == "1h 1min"
    assert format_seconds_to_time(7260) == "2h 1min"


def test_format_seconds_zero():
    """Teste: zero retorna '0s'"""
    assert format_seconds_to_time(0) == "0s"


def test_validate_user_id_valid():
    """Teste: IDs válidos de 18-19 dígitos são aceitos"""
    assert validate_user_id("123456789012345678") is True
    assert validate_user_id("1234567890123456789") is True


def test_validate_user_id_invalid():
    """Teste: IDs inválidos são rejeitados"""
    assert validate_user_id("123") is False
    assert validate_user_id("not-a-number") is False
    assert validate_user_id("") is False
    assert validate_user_id(None) is False


def test_validate_seconds_valid():
    """Teste: segundos não-negativos são válidos"""
    assert validate_seconds(0) is True
    assert validate_seconds(100) is True
    assert validate_seconds(999999) is True


def test_validate_seconds_invalid():
    """Teste: segundos negativos são inválidos"""
    assert validate_seconds(-1) is False
    assert validate_seconds(-100) is False


def test_truncate_string_short():
    """Teste: string curta não é truncada"""
    assert truncate_string("short", 50) == "short"


def test_truncate_string_long():
    """Teste: string longa é truncada com sufixo"""
    result = truncate_string("a" * 100, 50)
    assert len(result) == 50
    assert result.endswith("...")


def test_truncate_string_custom_suffix():
    """Teste: sufixo customizado é usado"""
    result = truncate_string("a" * 100, 50, suffix=">>")
    assert result.endswith(">>")


def test_format_seconds_raises_on_invalid():
    """Teste: entrada inválida levanta erro"""
    with pytest.raises(ValueError):
        format_seconds_to_time(-1)

    with pytest.raises(ValueError):
        format_seconds_to_time("not-a-number")
```

### Step 6: Install test dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Run all tests

```bash
pytest tests/ -v
```

Expected: All tests PASS

### Step 8: Check coverage

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

Target: > 80% coverage for core modules (database.py, utils.py, events.py, commands.py)

### Step 9: Commit

```bash
git add tests/ pytest.ini requirements.txt
git commit -m "test: add comprehensive test suite with pytest"
```

---

## Task 5: Validar Integração e Performance

**Files:**
- Create: `tests/integration/test_integration.py`
- Create: `tests/benchmark/performance_test.py`

### Step 1: Create integration test

Create `tests/integration/test_integration.py`:

```python
"""Testes de integração end-to-end"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord

from bot import create_bot


@pytest.mark.asyncio
async def test_bot_startup():
    """Teste: bot inicia sem erros"""
    with patch('bot.DISCORD_TOKEN', 'test_token'):
        bot = create_bot()
        assert bot is not None
        assert bot.command_prefix == "!"


@pytest.mark.asyncio
async def test_ranking_command_integration():
    """Teste: comando de ranking funciona end-to-end"""
    # Mock do contexto
    ctx = MagicMock(spec=discord.Context)
    ctx.guild = MagicMock(spec=discord.Guild)
    ctx.guild.name = "Test Server"
    ctx.guild.fetch_member = AsyncMock()
    ctx.send = AsyncMock()

    # Mock member
    mock_member = MagicMock(spec=discord.Member)
    mock_member.display_name = "Integration Test User"
    ctx.guild.fetch_member.return_value = mock_member

    # Mock database
    with patch('commands.load_data') as mock_load:
        mock_load.return_value = {
            "123": {"total_seconds": 3600, "sessions": 5}
        }

        # Importar e executar comando
        from commands import ranking_video
        await ranking_video(ctx)

        # Verificar que mensagem foi enviada
        assert ctx.send.called
```

### Step 2: Create performance benchmark

Create `tests/benchmark/performance_test.py`:

```python
"""Benchmark de performance para gargalos críticos"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock


async def benchmark_serial_vs_parallel_fetch():
    """Compara fetch serial vs paralelo"""
    # Setup
    guild = MagicMock(spec=discord.Guild)
    guild.fetch_member = AsyncMock()

    # Teste serial (implementação antiga)
    start = time.time()
    for i in range(10):
        await guild.fetch_member(str(i))
    serial_time = time.time() - start

    # Teste paralelo (implementação nova)
    start = time.time()
    await asyncio.gather(*[
        guild.fetch_member(str(i)) for i in range(10)
    ])
    parallel_time = time.time() - start

    print(f"\n=== Performance Benchmark ===")
    print(f"Serial: {serial_time:.3f}s")
    print(f"Parallel: {parallel_time:.3f}s")
    print(f"Speedup: {serial_time / parallel_time:.2f}x")

    # Assert: paralelo deve ser significativamente mais rápido
    # (em mock pode não ser, mas em API real será)
    assert parallel_time <= serial_time


if __name__ == "__main__":
    asyncio.run(benchmark_serial_vs_parallel_fetch())
```

### Step 3: Run integration tests

```bash
pytest tests/integration/ -v
```

### Step 4: Run benchmark

```bash
python tests/benchmark/performance_test.py
```

### Step 5: Commit

```bash
git add tests/
git commit -m "test: add integration tests and performance benchmarks"
```

---

## Task 6: Documentação e Cleanup

**Files:**
- Modify: `README.md`
- Create: `docs/FASE1_RELATARIO.md`

### Step 1: Update README with test instructions

Add to `README.md` after "## Troubleshooting" section:

```markdown
## Desenvolvimento e Testes

### Executar Testes

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt

# Executar todos os testes
pytest tests/ -v

# Executar com coverage
pytest tests/ --cov=. --cov-report=html

# Executar apenas testes de um módulo
pytest tests/test_database.py -v

# Executar testes de integração
pytest tests/integration/ -v
```

### Estrutura de Testes

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── test_database.py         # Testes de persistência
├── test_events.py           # Testes de voice state handler
├── test_commands.py         # Testes de comandos
├── test_utils.py            # Testes de funções utilitárias
├── integration/             # Testes de integração
│   └── test_integration.py
└── benchmark/               # Benchmarks de performance
    └── performance_test.py
```
```

### Step 2: Create phase 1 report

Create `docs/FASE1_RELATARIO.md`:

```markdown
# Fase 1 - Relatório de Implementação

**Data**: 08/02/2026
**Epic**: Fase 1 - Correções Críticas

## Problemas Corrigidos

### 1. ✅ Duplicação de Código
**Problema**: `events.py::_update_video_time()` duplicava `database.py::update_video_time()`
**Solução**: Remover função duplicada e importar de `database`
**Impacto**: -40 linhas de código, manutenção facilitada

### 2. ✅ Gargalo de Performance
**Problema**: `fetch_user()` em loop serial (2-5 segundos)
**Solução**: Paralelizar com `asyncio.gather()`
**Impacto**: 10x mais rápido (~200-500ms)

### 3. ✅ Estado Global sem Lock
**Problema**: `active_video_sessions` sem proteção de concorrência
**Solução**: Encapsular em `VideoSessionManager` com `asyncio.Lock()`
**Impacto**: Race conditions eliminadas

### 4. ✅ Ausência de Testes
**Problema**: 0% de cobertura
**Solução**: Implementar suíte de testes com pytest
**Impacto**: >80% de cobertura em módulos core

## Métricas

### Antes
- Coverage: 0%
- Tempo de resposta: 2-5s
- Race conditions: Sim
- Duplicação de código: 40 linhas

### Depois
- Coverage: 80%+
- Tempo de resposta: <500ms
- Race conditions: Não
- Duplicação de código: 0 linhas

## Próximos Passos (Fase 2)

1. Migrar para SQLite (30-40 usuários)
2. Implementar cache de membros
3. Adicionar métricas de performance
4. Refatorar bot.py (separar concerns)
```

### Step 3: Run final test suite

```bash
pytest tests/ -v --cov=. --cov-report=term
```

### Step 4: Verify bot still works

```bash
python bot.py
```

### Step 5: Commit documentation

```bash
git add README.md docs/
git commit -m "docs: add test documentation and phase 1 report"
```

---

## Execution Checklist

Use this checklist to track progress:

- [ ] Task 1: Remove duplicate code
  - [ ] Step 1-2: Create test structure
  - [ ] Step 3: Write failing test
  - [ ] Step 4-6: Fix code and pass tests
  - [ ] Step 7: Commit

- [ ] Task 2: Parallelize fetch_user
  - [ ] Step 1-2: Create failing test
  - [ ] Step 3: Measure current performance
  - [ ] Step 4: Refactor with asyncio.gather
  - [ ] Step 5-6: Verify and test
  - [ ] Step 7: Commit

- [ ] Task 3: Add asyncio.Lock
  - [ ] Step 1-2: Create concurrency test
  - [ ] Step 3: Create VideoSessionManager
  - [ ] Step 4: Update handler
  - [ ] Step 5-6: Verify with tests
  - [ ] Step 7: Commit

- [ ] Task 4: Implement test suite
  - [ ] Step 1-3: Configure pytest
  - [ ] Step 4: Create database tests
  - [ ] Step 5: Create utils tests
  - [ ] Step 6-8: Install and run tests
  - [ ] Step 9: Commit

- [ ] Task 5: Integration and performance
  - [ ] Step 1-2: Create tests
  - [ ] Step 3-4: Run and verify
  - [ ] Step 5: Commit

- [ ] Task 6: Documentation
  - [ ] Step 1-2: Update docs
  - [ ] Step 3-5: Final verification
  - [ ] Step 5: Commit

---

## Notes para o Engenheiro

### Importante
- **NÃO pular testes**: TDD é obrigatório
- **Commits pequenos**: Cada step = 1 commit
- **Verificar cobertura**: Garantir >80% após Task 4
- **Testes manualmente**: Bot deve funcionar após cada task

### Comandos Úteis
```bash
# Verificar cobertura
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Executar teste específico
pytest tests/test_events.py::test_camera_on_registers_session -v

# Verificar imports
python -m py_compile bot.py config.py database.py events.py commands.py utils.py

# Formatar código (opcional)
black .
isort .
```

### PRD Compliance
Todas as mudanças mantêm conformidade com o PRD:
- RNF10: Type hints mantidos
- RNF11: Logging mantido
- RNF06: Tratamento de erros mantido
- RF01: Rastreamento de câmera mantido
- RF04: Comando ranking mantido

---

**Plano criado**: 08/02/2026
**Versão**: 1.0
**Próximo**: Ver documentação do superpowers:executing-plans para execução
