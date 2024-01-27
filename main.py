#!/usr/bin/env python3
import asyncio
import random

from constants import GMK67_VID, GMK67_PID, ROWS
from controller import RGBColor, GMK67Controller


def random_color() -> RGBColor:
    return RGBColor(
        red=random.randint(0, 255),
        green=random.randint(0, 255),
        blue=random.randint(0, 255)
    )


colors = {}


async def randomize_colors() -> None:
    while True:
        for row in ROWS:
            row_color = random_color()
            for position in row:
                colors[position] = row_color
        await asyncio.sleep(10)


async def control() -> None:
    with GMK67Controller(GMK67_VID, GMK67_PID) as c:
        while True:
            c.send_direct(colors)
            await asyncio.sleep(0.4)


async def main():
    await asyncio.gather(randomize_colors(), control())


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Exiting.")
