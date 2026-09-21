import math
import sys
import time


def run(seconds: int = 120) -> None:
    end = time.monotonic() + seconds
    value = 0.0
    while time.monotonic() < end:
        for index in range(100_000):
            value += math.sin(index) * math.cos(index / 3)
    print(f"SmartLab demo workload complete: {value:.3f}")


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 120)

