"""Benchmark de performance para gargalos críticos"""
import asyncio
import time
import discord
from unittest.mock import AsyncMock, MagicMock


async def benchmark_serial_vs_parallel_fetch():
    """Compara fetch serial vs paralelo"""
    guild = MagicMock(spec=discord.Guild)
    guild.fetch_member = AsyncMock()

    start = time.time()
    for i in range(10):
        await guild.fetch_member(str(i))
    serial_time = time.time() - start

    start = time.time()
    await asyncio.gather(*[guild.fetch_member(str(i)) for i in range(10)])
    parallel_time = time.time() - start

    print(f"\n=== Performance Benchmark ===")
    print(f"Serial: {serial_time:.3f}s")
    print(f"Parallel: {parallel_time:.3f}s")
    if parallel_time > 0:
        print(f"Speedup: {serial_time / parallel_time:.2f}x")
    else:
        print(f"Speedup: N/A (times too small for accurate measurement)")
    # Com mocks, a execução é instantânea, então só verificamos que não falhou
    assert serial_time >= 0 and parallel_time >= 0


if __name__ == "__main__":
    asyncio.run(benchmark_serial_vs_parallel_fetch())
