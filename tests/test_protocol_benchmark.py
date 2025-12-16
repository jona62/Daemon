"""Benchmark tests for protocol performance."""

import time
import pytest
from task_daemon.protocols import JSONProtocol, MessagePackProtocol


def generate_test_data(size="small"):
    """Generate test data of various sizes."""
    if size == "small":
        return {"id": 1, "name": "test", "value": 42}
    elif size == "medium":
        return {
            "id": 1,
            "name": "test_task",
            "data": list(range(100)),
            "metadata": {"key": "value", "nested": {"a": 1, "b": 2}},
        }
    elif size == "large":
        return {
            "id": 1,
            "name": "large_task",
            "data": list(range(1000)),
            "nested": [{"id": i, "value": i * 2} for i in range(100)],
        }


def benchmark_protocol(protocol, data, iterations=1000):
    """Benchmark serialization and deserialization."""
    # Warmup
    for _ in range(10):
        serialized = protocol.serialize(data)
        protocol.deserialize(serialized)

    # Serialize benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        serialized = protocol.serialize(data)
    serialize_time = time.perf_counter() - start

    # Deserialize benchmark
    serialized = protocol.serialize(data)
    start = time.perf_counter()
    for _ in range(iterations):
        protocol.deserialize(serialized)
    deserialize_time = time.perf_counter() - start

    # Size
    size = len(serialized)

    return {
        "serialize_time": serialize_time,
        "deserialize_time": deserialize_time,
        "total_time": serialize_time + deserialize_time,
        "size": size,
        "iterations": iterations,
    }


@pytest.mark.benchmark
def test_protocol_benchmark_small():
    """Benchmark protocols with small data."""
    data = generate_test_data("small")

    json_protocol = JSONProtocol()
    msgpack_protocol = MessagePackProtocol()

    json_results = benchmark_protocol(json_protocol, data)
    msgpack_results = benchmark_protocol(msgpack_protocol, data)

    print("\n" + "=" * 70)
    print("SMALL DATA BENCHMARK")
    print("=" * 70)
    print(f"Data: {data}")
    print(f"\nJSON:")
    print(f"  Serialize:   {json_results['serialize_time']:.4f}s")
    print(f"  Deserialize: {json_results['deserialize_time']:.4f}s")
    print(f"  Total:       {json_results['total_time']:.4f}s")
    print(f"  Size:        {json_results['size']} bytes")
    print(f"\nMessagePack:")
    print(f"  Serialize:   {msgpack_results['serialize_time']:.4f}s")
    print(f"  Deserialize: {msgpack_results['deserialize_time']:.4f}s")
    print(f"  Total:       {msgpack_results['total_time']:.4f}s")
    print(f"  Size:        {msgpack_results['size']} bytes")
    print(f"\nSpeedup:")
    print(
        f"  Serialize:   {json_results['serialize_time'] / msgpack_results['serialize_time']:.2f}x"
    )
    print(
        f"  Deserialize: {json_results['deserialize_time'] / msgpack_results['deserialize_time']:.2f}x"
    )
    print(
        f"  Total:       {json_results['total_time'] / msgpack_results['total_time']:.2f}x"
    )
    print(f"  Size:        {json_results['size'] / msgpack_results['size']:.2f}x")

    # Assertions
    assert msgpack_results["total_time"] < json_results["total_time"]
    assert msgpack_results["size"] <= json_results["size"]


@pytest.mark.benchmark
def test_protocol_benchmark_medium():
    """Benchmark protocols with medium data."""
    data = generate_test_data("medium")

    json_protocol = JSONProtocol()
    msgpack_protocol = MessagePackProtocol()

    json_results = benchmark_protocol(json_protocol, data)
    msgpack_results = benchmark_protocol(msgpack_protocol, data)

    print("\n" + "=" * 70)
    print("MEDIUM DATA BENCHMARK")
    print("=" * 70)
    print(f"\nJSON:")
    print(f"  Serialize:   {json_results['serialize_time']:.4f}s")
    print(f"  Deserialize: {json_results['deserialize_time']:.4f}s")
    print(f"  Total:       {json_results['total_time']:.4f}s")
    print(f"  Size:        {json_results['size']} bytes")
    print(f"\nMessagePack:")
    print(f"  Serialize:   {msgpack_results['serialize_time']:.4f}s")
    print(f"  Deserialize: {msgpack_results['deserialize_time']:.4f}s")
    print(f"  Total:       {msgpack_results['total_time']:.4f}s")
    print(f"  Size:        {msgpack_results['size']} bytes")
    print(f"\nSpeedup:")
    print(
        f"  Serialize:   {json_results['serialize_time'] / msgpack_results['serialize_time']:.2f}x"
    )
    print(
        f"  Deserialize: {json_results['deserialize_time'] / msgpack_results['deserialize_time']:.2f}x"
    )
    print(
        f"  Total:       {json_results['total_time'] / msgpack_results['total_time']:.2f}x"
    )
    print(f"  Size:        {json_results['size'] / msgpack_results['size']:.2f}x")

    assert msgpack_results["total_time"] < json_results["total_time"]
    assert msgpack_results["size"] < json_results["size"]


@pytest.mark.benchmark
def test_protocol_benchmark_large():
    """Benchmark protocols with large data."""
    data = generate_test_data("large")

    json_protocol = JSONProtocol()
    msgpack_protocol = MessagePackProtocol()

    json_results = benchmark_protocol(json_protocol, data, iterations=100)
    msgpack_results = benchmark_protocol(msgpack_protocol, data, iterations=100)

    print("\n" + "=" * 70)
    print("LARGE DATA BENCHMARK")
    print("=" * 70)
    print(f"\nJSON:")
    print(f"  Serialize:   {json_results['serialize_time']:.4f}s")
    print(f"  Deserialize: {json_results['deserialize_time']:.4f}s")
    print(f"  Total:       {json_results['total_time']:.4f}s")
    print(f"  Size:        {json_results['size']} bytes")
    print(f"\nMessagePack:")
    print(f"  Serialize:   {msgpack_results['serialize_time']:.4f}s")
    print(f"  Deserialize: {msgpack_results['deserialize_time']:.4f}s")
    print(f"  Total:       {msgpack_results['total_time']:.4f}s")
    print(f"  Size:        {msgpack_results['size']} bytes")
    print(f"\nSpeedup:")
    print(
        f"  Serialize:   {json_results['serialize_time'] / msgpack_results['serialize_time']:.2f}x"
    )
    print(
        f"  Deserialize: {json_results['deserialize_time'] / msgpack_results['deserialize_time']:.2f}x"
    )
    print(
        f"  Total:       {json_results['total_time'] / msgpack_results['total_time']:.2f}x"
    )
    print(f"  Size:        {json_results['size'] / msgpack_results['size']:.2f}x")
    print("=" * 70)

    assert msgpack_results["total_time"] < json_results["total_time"]
    assert msgpack_results["size"] < json_results["size"]


def test_protocol_correctness():
    """Test that both protocols produce correct results."""
    test_data = {
        "string": "hello",
        "number": 42,
        "float": 3.14,
        "bool": True,
        "null": None,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
    }

    json_protocol = JSONProtocol()
    msgpack_protocol = MessagePackProtocol()

    # JSON roundtrip
    json_serialized = json_protocol.serialize(test_data)
    json_deserialized = json_protocol.deserialize(json_serialized)
    assert json_deserialized == test_data

    # MessagePack roundtrip
    msgpack_serialized = msgpack_protocol.serialize(test_data)
    msgpack_deserialized = msgpack_protocol.deserialize(msgpack_serialized)
    assert msgpack_deserialized == test_data
