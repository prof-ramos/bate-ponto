"""
Módulo de persistência de dados para o bot de ranking Discord.

Este módulo implementa funções para carregar, salvar e atualizar
dados de ranking de tempo de câmera no formato JSON, conforme
RF06 e seção 4.4.2 do PRD.
"""

from pathlib import Path
from typing import Dict, Any
import json


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
    if not DATA_FILE.exists():
        # Criar arquivo vazio conforme RF06
        save_data({})
        return {}
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Validar estrutura básica
            if not isinstance(data, dict):
                return {}
            return data
    except (json.JSONDecodeError, ValueError):
        # Arquivo corrompido - recriar vazio
        save_data({})
        return {}


def save_data(data: Dict[str, Dict[str, int]]) -> None:
    """
    Salva os dados de ranking no arquivo JSON.
    
    Conforme RNF12: Usa indent=2 para legibilidade do arquivo JSON.
    
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
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_video_time(user_id: str, duration: int) -> None:
    """
    Atualiza o tempo acumulado de câmera para um usuário.
    
    Carrega os dados atuais, adiciona a duração ao total do usuário
    e incrementa o contador de sessões. Salva o arquivo atualizado.
    
    Args:
        user_id: ID do usuário Discord (string)
        duration: Duração da sessão em segundos (int > 0)
    
    Raises:
        ValueError: Se duration for negativo
    
    Example:
        >>> update_video_time("123456789", 1800)  # 30 minutos
        >>> data = load_data()
        >>> data["123456789"]["sessions"]
        1
    """
    if duration < 0:
        raise ValueError("duration must be non-negative")
    
    data = load_data()
    
    if user_id not in data:
        # Nova entrada para o usuário
        data[user_id] = {
            "total_seconds": duration,
            "sessions": 1
        }
    else:
        # Atualizar entrada existente
        data[user_id]["total_seconds"] += duration
        data[user_id]["sessions"] += 1
    
    save_data(data)


# Inicialização: criar arquivo vazio se não existir
if not DATA_FILE.exists():
    save_data({})
