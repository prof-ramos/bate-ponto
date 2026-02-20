"""
Módulo de bloqueio de arquivos para operações de banco de dados seguras.

Este módulo implementa mecanismos de bloqueio de arquivos para garantir
operações atômicas e seguras em operações de leitura/escrita de JSON.
"""

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Optional

try:
    import portalocker
except ImportError:
    portalocker = None


class FileLockError(Exception):
    """Exceção levantada quando ocorre erro no bloqueio de arquivo."""
    pass


@contextmanager
def acquire_file_lock(file_path: str, timeout: int = 30, mode: str = 'r+'):
    """
    Context manager para adquirir bloqueio de arquivo.
    
    Args:
        file_path: Caminho do arquivo a ser bloqueado
        timeout: Tempo máximo de espera para adquirir o bloqueio (segundos)
        mode: Modo de abertura do arquivo ('r', 'w', 'r+', etc.)
    
    Yields:
        File object: Arquivo aberto e bloqueado
        
    Raises:
        FileLockError: Se não conseguir adquirir o bloqueio no tempo especificado
    """
    if portalocker is None:
        raise FileLockError("portalocker não está instalado. Instale com: pip install portalocker")
    
    file_obj = None
    start_time = time.time()
    
    try:
        # Abrir arquivo no modo especificado
        file_obj = open(file_path, mode, encoding='utf-8')
        
        # Tentar adquirir bloqueio com timeout
        while True:
            try:
                portalocker.lock(file_obj, portalocker.LOCK_EX | portalocker.LOCK_NB)
                break  # Bloqueio adquirido com sucesso
            except portalocker.LockException:
                if time.time() - start_time > timeout:
                    raise FileLockError(f"Timeout ao tentar bloquear arquivo: {file_path}")
                time.sleep(0.1)  # Pequeno delay antes de tentar novamente
        
        yield file_obj
        
    except Exception as e:
        if isinstance(e, FileLockError):
            raise
        raise FileLockError(f"Erro ao manipular arquivo {file_path}: {e}")
    
    finally:
        if file_obj:
            try:
                portalocker.unlock(file_obj)
                file_obj.close()
            except Exception as e:
                # Log error but don't raise in finally block
                import logging
                logging.getLogger("bate-ponto").warning(f"Error closing file {file_path}: {e}")


def atomic_write_json(data: Dict[str, Any], file_path: str, timeout: int = 30) -> None:
    """
    Escreve dados JSON de forma atômica com bloqueio de arquivo.

    Args:
        data: Dados a serem escritos no formato JSON
        file_path: Caminho do arquivo JSON
        timeout: Tempo máximo de espera para bloqueio (segundos)

    Raises:
        FileLockError: Se não conseguir bloquear o arquivo
        json.JSONDecodeError: Se os dados não forem serializáveis em JSON
    """
    # Validar dados
    if not isinstance(data, dict):
        raise ValueError("Os dados devem ser um dicionário")

    # Garantir que o diretório existe
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    # Temp file no mesmo diretório para garantir atomic rename
    file_path_obj = Path(file_path)
    temp_file_path = str(file_path_obj.with_suffix(file_path_obj.suffix + '.tmp'))

    try:
        # Adquirir lock e escrever de forma atômica
        with acquire_file_lock(file_path, timeout=timeout, mode='r+'):
            # Escrever no arquivo temporário primeiro
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Usar os.replace em vez de os.rename (funciona em todos os sistemas)
            os.replace(temp_file_path, file_path)

    except Exception as e:
        # Limpar arquivo temporário em caso de erro
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as cleanup_error:
                import logging
                logging.getLogger("bate-ponto").warning(f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}")
        raise FileLockError(f"Erro ao escrever arquivo JSON: {e}")


def safe_load_json(file_path: str, default_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Carrega dados JSON de forma segura com bloqueio de leitura.

    Args:
        file_path: Caminho do arquivo JSON
        default_data: Dados padrão se o arquivo não existir ou estiver corrompido

    Returns:
        Dict: Dados carregados do arquivo ou dados padrão
    """
    if default_data is None:
        default_data = {}

    if not os.path.exists(file_path):
        return default_data.copy()

    try:
        # Usar o file handle retornado pelo lock em vez de re-abrir o arquivo
        with acquire_file_lock(file_path, mode='r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return default_data.copy()
            return data
    except (json.JSONDecodeError, FileLockError, FileNotFoundError):
        return default_data.copy()
    except Exception as e:
        raise FileLockError(f"Erro ao carregar arquivo JSON: {e}")


def safe_update_json(
    file_path: str,
    update_func: Callable[[Dict[str, Any]], Dict[str, Any]],
    timeout: int = 30,
    default_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Atualiza dados JSON de forma segura com bloqueio exclusivo.

    Corrige TOCTOU race condition mantendo o lock durante toda a operação
    read-modify-write.

    Args:
        file_path: Caminho do arquivo JSON
        update_func: Função que recebe os dados atuais e retorna os dados atualizados
        timeout: Tempo máximo de espera para bloqueio (segundos)
        default_data: Dados padrão se o arquivo não existir

    Returns:
        Dict: Dados atualizados após a operação

    Raises:
        FileLockError: Se não conseguir bloquear o arquivo
    """
    if default_data is None:
        default_data = {}

    try:
        # Adquirir lock para toda operação read-modify-write (evita TOCTOU)
        with acquire_file_lock(file_path, timeout=timeout, mode='r+') as f:
            # Ler dados atuais
            try:
                f.seek(0)
                data = json.load(f)
                if not isinstance(data, dict):
                    data = default_data.copy()
            except (json.JSONDecodeError, ValueError):
                data = default_data.copy()

            # Aplicar atualização
            updated_data = update_func(data)

            # Escrever de volta ao arquivo (com truncate)
            f.seek(0)
            json.dump(updated_data, f, indent=2, ensure_ascii=False)
            f.truncate()

            return updated_data

    except Exception as e:
        raise FileLockError(f"Erro ao atualizar arquivo JSON: {e}")