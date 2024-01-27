#!/usr/bin/env python3
from time import sleep

from constants import LightingModes, GMK67_VID, GMK67_PID
from controller import GMK67Controller


def demo_modes():
    with GMK67Controller(GMK67_VID, GMK67_PID) as c:
        try:
            for value in LightingModes:
                while True:
                    print(f"Displaying LightningMode: {value.name}")
                    c.update_mode(value)
                    sleep(0.5)
                    inp = input("Press N to continue\n")
                    if "N" in inp:
                        break
        except KeyboardInterrupt:
            pass


demo_modes()
