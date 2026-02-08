"""Benchmark para medir melhoria de performance"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock


async def mock_fetch_member_with_delay(user_id):
    """Simula fetch_member com delay de rede (aprox 200ms por chamada)"""
    await asyncio.sleep(0.2)  # 200ms de delay
    return MagicMock(display_name=f"User_{user_id}")


async def benchmark_serial():
    """Simula implementação serial atual"""
    mock_guild = MagicMock()
    mock_guild.fetch_member = mock_fetch_member_with_delay

    start = time.time()
    for i in range(10):
        await mock_guild.fetch_member(str(i))
    elapsed = time.time() - start
    return elapsed


async def benchmark_parallel():
    """Simula implementação paralela"""
    mock_guild = MagicMock()
    mock_guild.fetch_member = mock_fetch_member_with_delay

    start = time.time()
    await asyncio.gather(*[
        mock_guild.fetch_member(str(i)) for i in range(10)
    ])
    elapsed = time.time() - start
    return elapsed


async def main():
    print("=" * 60)
    print("Benchmark: Serial vs Parallel fetch_user")
    print("=" * 60)
    print(f"Número de chamadas: 10")
    print(f"Delay simulado por chamada: 200ms")
    print("-" * 60)

    # Executar benchmarks
    serial_time = await benchmark_serial()
    print(f"Serial (atual):        {serial_time:.4f}s")

    parallel_time = await benchmark_parallel()
    print(f"Parallel (novo):       {parallel_time:.4f}s")

    # Calcular melhoria
    speedup = serial_time / parallel_time
    improvement = ((serial_time - parallel_time) / serial_time) * 100

    print("-" * 60)
    print(f"Speedup:                {speedup:.2f}x")
    print(f"Melhoria:               {improvement:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
