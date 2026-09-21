import asyncio
import logging

from .client import AgentClient
from .config import AgentConfig
from .monitor import Monitor


async def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = AgentConfig.load()
    monitor = Monitor()
    if not config.device_id:
        config.device_id = monitor.system_identity()["device_id"]
        config.save()
    await AgentClient(config, monitor).run()


if __name__ == "__main__":
    asyncio.run(run())

