"""Tests para database.py - persistência de dados."""
import pytest
import json
from pathlib import Path
from database import load_data, save_data, update_video_time, DATA_FILE


class TestLoadData:
    """Testes para função load_data."""

    def test_load_data_creates_empty_file_if_not_exists(self, temp_data_file):
        """Teste: cria arquivo vazio se não existir."""
        # Remover arquivo se existir
        if temp_data_file.exists():
            temp_data_file.unlink()

        # Importar novamente para usar o novo DATA_FILE
        from database import DATA_FILE
        DATA_FILE = temp_data_file

        # Carregar dados deve criar arquivo vazio
        data = load_data()

        assert data == {}
        assert temp_data_file.exists()

    def test_load_data_returns_empty_dict_for_empty_file(self, temp_data_file):
        """Teste: retorna dict vazio para arquivo vazio."""
        temp_data_file.write_text("{}")

        data = load_data()

        assert data == {}

    def test_load_data_returns_correct_data(self, temp_data_file, sample_data):
        """Teste: retorna dados corretos do arquivo."""
        temp_data_file.write_text(json.dumps(sample_data))

        data = load_data()

        assert data == sample_data
        assert "123456789012345678" in data
        assert data["123456789012345678"]["total_seconds"] == 3600

    def test_load_data_handles_corrupted_json(self, temp_data_file):
        """Teste: trata JSON corrompido recriando arquivo vazio."""
        temp_data_file.write_text("{invalid json content")

        data = load_data()

        assert data == {}
        # Arquivo deve ter sido recriado com JSON válido
        assert json.loads(temp_data_file.read_text()) == {}

    def test_load_data_handles_invalid_structure(self, temp_data_file):
        """Teste: trata estrutura inválida retornando dict vazio."""
        temp_data_file.write_text('"not a dict"')

        data = load_data()

        assert data == {}


class TestSaveData:
    """Testes para função save_data."""

    def test_save_data_writes_valid_json(self, temp_data_file, sample_data):
        """Teste: escreve JSON válido no arquivo."""
        save_data(sample_data)

        with open(temp_data_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data == sample_data

    def test_save_data_uses_indentation(self, temp_data_file):
        """Teste: usa indentação conforme RNF12."""
        test_data = {"123": {"total_seconds": 100, "sessions": 1}}
        save_data(test_data)

        content = temp_data_file.read_text()

        # Verificar que o arquivo está formatado com indentação
        assert "\n" in content
        assert "  " in content  # 2 espaços de indentação

    def test_save_data_handles_unicode(self, temp_data_file):
        """Teste: lida corretamente com caracteres Unicode."""
        test_data = {
            "123": {
                "total_seconds": 100,
                "sessions": 1,
                "name": "João São"
            }
        }
        save_data(test_data)

        with open(temp_data_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        assert loaded_data["123"]["name"] == "João São"

    def test_save_data_overwrites_existing_content(self, temp_data_file):
        """Teste: sobrescreve conteúdo existente."""
        # Escrever dados iniciais
        initial_data = {"111": {"total_seconds": 50, "sessions": 1}}
        save_data(initial_data)

        # Escrever novos dados
        new_data = {"222": {"total_seconds": 100, "sessions": 2}}
        save_data(new_data)

        # Verificar que apenas os novos dados existem
        with open(temp_data_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data == new_data
        assert "111" not in loaded_data


class TestUpdateVideoTime:
    """Testes para função update_video_time."""

    def test_update_video_time_creates_new_user(self, temp_data_file):
        """Teste: cria nova entrada para usuário inexistente."""
        temp_data_file.write_text("{}")

        update_video_time("123456789012345678", 1800)

        data = load_data()
        assert "123456789012345678" in data
        assert data["123456789012345678"]["total_seconds"] == 1800
        assert data["123456789012345678"]["sessions"] == 1

    def test_update_video_time_updates_existing_user(self, temp_data_file):
        """Teste: atualiza entrada de usuário existente."""
        initial_data = {
            "123456789012345678": {
                "total_seconds": 1000,
                "sessions": 2
            }
        }
        temp_data_file.write_text(json.dumps(initial_data))

        update_video_time("123456789012345678", 500)

        data = load_data()
        assert data["123456789012345678"]["total_seconds"] == 1500
        assert data["123456789012345678"]["sessions"] == 3

    def test_update_video_time_adds_duration(self, temp_data_file):
        """Teste: adiciona duração ao tempo total."""
        initial_data = {
            "123456789012345678": {
                "total_seconds": 3600,
                "sessions": 5
            }
        }
        temp_data_file.write_text(json.dumps(initial_data))

        update_video_time("123456789012345678", 7200)

        data = load_data()
        assert data["123456789012345678"]["total_seconds"] == 10800
        assert data["123456789012345678"]["sessions"] == 6

    def test_update_video_time_increments_sessions(self, temp_data_file):
        """Teste: incrementa contador de sessões."""
        initial_data = {
            "123456789012345678": {
                "total_seconds": 1000,
                "sessions": 1
            }
        }
        temp_data_file.write_text(json.dumps(initial_data))

        # Adicionar 3 sessões
        update_video_time("123456789012345678", 100)
        update_video_time("123456789012345678", 200)
        update_video_time("123456789012345678", 300)

        data = load_data()
        assert data["123456789012345678"]["sessions"] == 4
        assert data["123456789012345678"]["total_seconds"] == 1600

    def test_update_video_time_rejects_negative_duration(self, temp_data_file):
        """Teste: rejeita duração negativa."""
        with pytest.raises(ValueError, match="duration must be non-negative"):
            update_video_time("123456789012345678", -100)

    def test_update_video_time_accepts_zero_duration(self, temp_data_file):
        """Teste: aceita duração zero."""
        temp_data_file.write_text("{}")

        update_video_time("123456789012345678", 0)

        data = load_data()
        assert data["123456789012345678"]["total_seconds"] == 0
        assert data["123456789012345678"]["sessions"] == 1

    def test_update_video_time_handles_large_durations(self, temp_data_file):
        """Teste: lida com durações grandes (ex: sessão de 24h)."""
        temp_data_file.write_text("{}")

        # 24 horas em segundos
        large_duration = 24 * 60 * 60
        update_video_time("123456789012345678", large_duration)

        data = load_data()
        assert data["123456789012345678"]["total_seconds"] == large_duration

    def test_update_video_time_multiple_users(self, temp_data_file):
        """Teste: atualiza múltiplos usuários corretamente."""
        temp_data_file.write_text("{}")

        update_video_time("111111111111111111", 1000)
        update_video_time("222222222222222222", 2000)
        update_video_time("111111111111111111", 500)

        data = load_data()
        assert data["111111111111111111"]["total_seconds"] == 1500
        assert data["222222222222222222"]["total_seconds"] == 2000
        assert data["111111111111111111"]["sessions"] == 2
        assert data["222222222222222222"]["sessions"] == 1
