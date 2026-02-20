"""
Módulo de persistência de dados para o bot de ranking Discord.

Este módulo implementa funções para carregar, salvar e atualizar
dados de ranking de tempo de câmera no formato JSON, conforme
RF06 e seção 4.4.2 do PRD.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

# Importar módulo de bloqueio de arquivos
from database_lock import (
    safe_load_json,
    atomic_write_json,
    safe_update_json,
    FileLockError
)


# Caminho do arquivo JSON de dados
DATA_FILE = Path("video_ranking.json")


def load_data() -> Dict[str, Dict[str, int]]:
    """
    Carrega os dados de ranking do arquivo JSON.

    Conforme RF06: Lê o arquivo video_ranking.json e retorna
    o dicionário com dados de todos os usuários.

    Returns:
        Dict[str, Dict[str, int]]: Dicionário onde a chave é o user_id
            e o valor é um dict com 'total_seconds' e 'sessions'.
            Retorna dict vazio se arquivo não existir ou estiver vazio.

    Example:
        >>> data = load_data()
        >>> data["123456789"]
        {'total_seconds': 3600, 'sessions': 5}
    """
    # Criar arquivo vazio se não existir
    if not DATA_FILE.exists():
        _ensure_data_file_exists()

    return safe_load_json(str(DATA_FILE), {})


def _ensure_data_file_exists(max_retries: int = 3) -> None:
    """
    Garante que o arquivo de dados existe, criando-o se necessário.

    Implementa retry logic com exponential backoff para evitar
    condições de corrida durante a criação do arquivo.

    Args:
        max_retries: Número máximo de tentativas de criação
    """
    for attempt in range(max_retries):
        try:
            # Verificar novamente se o arquivo já existe
            if DATA_FILE.exists():
                # Verificar se o arquivo é non-empty
                if DATA_FILE.stat().st_size > 0:
                    return

            # Tentar criar arquivo vazio
            atomic_write_json({}, str(DATA_FILE))
            return

        except FileLockError:
            # Retry com exponential backoff
            if attempt < max_retries - 1:
                wait_time = 0.1 * (2 ** attempt)  # 0.1s, 0.2s, 0.4s
                time.sleep(wait_time)
            else:
                # Última tentativa: criar sem lock como fallback
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=2, ensure_ascii=False)


def save_data(data: Dict[str, Dict[str, int]]) -> None:
    """
    Salva os dados de ranking no arquivo JSON.
    
    Conforme RNF12: Usa indent=2 para legibilidade do arquivo JSON.
    Implementa operação atômica com bloqueio de arquivo.
    
    Args:
        data: Dicionário com dados dos usuários no formato:
            {
                "user_id": {
                    "total_seconds": int,
                    "sessions": int
                }
            }
    
    Example:
        >>> save_data({"123": {"total_seconds": 100, "sessions": 1}})
    """
    try:
        atomic_write_json(data, str(DATA_FILE))
    except FileLockError as e:
        raise RuntimeError(f"Erro ao salvar dados: {e}")


def update_video_time(user_id: str, duration: int) -> None:
    """
    Atualiza o tempo acumulado de câmera para um usuário.
    
    Carrega os dados atuais, adiciona a duração ao total do usuário
    e incrementa o contador de sessões. Salva o arquivo atualizado.
    Implementa operação atômica com bloqueio de arquivo.
    
    Args:
        user_id: ID do usuário Discord (string)
        duration: Duração da sessão em segundos (int > 0)
    
    Raises:
        ValueError: Se duration for negativo
        RuntimeError: Se ocorrer erro no bloqueio de arquivo
    
    Example:
        >>> update_video_time("123456789", 1800)  # 30 minutos
        >>> data = load_data()
        >>> data["123456789"]["sessions"]
        1
    """
    if duration < 0:
        raise ValueError("duration must be non-negative")
    
    def update_func(current_data: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
        """Função de atualização para safe_update_json."""
        if user_id not in current_data:
            # Nova entrada para o usuário
            current_data[user_id] = {
                "total_seconds": duration,
                "sessions": 1
            }
        else:
            # Atualizar entrada existente
            current_data[user_id]["total_seconds"] += duration
            current_data[user_id]["sessions"] += 1
        
        return current_data
    
    try:
        safe_update_json(str(DATA_FILE), update_func)
    except FileLockError as e:
        raise RuntimeError(f"Erro ao atualizar dados: {e}")


# Inicialização: criar arquivo vazio se não existir
if not DATA_FILE.exists():
    try:
        atomic_write_json({}, str(DATA_FILE))
    except FileLockError:
        # Se falhar o bloqueio, tentar criar sem bloqueio (fallback)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
