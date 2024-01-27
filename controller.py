import dataclasses

import hid

from constants import Constants, Commands, LightingModes, GMK67, POSITION_TO_MEMORY_LOCATION


@dataclasses.dataclass
class RGBColor:
    red: int
    green: int
    blue: int


class GMK67Controller:
    def __init__(self, vid, pid):
        self.device = hid.Device(vid, pid)

    def __enter__(self):
        print("Opening connection")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Closing connection")
        self.device.close()

    def send(self, data: bytearray | memoryview) -> None:
        packet = bytearray([Constants.REPORT_ID])
        packet.extend(data[:Constants.PACKET_DATA_LENGTH])
        self.device.send_feature_report(bytes(packet))

    def read(self) -> bytearray:
        return self.device.get_feature_report(Constants.REPORT_ID, Constants.PACKET_DATA_LENGTH + 1)

    def send_packet(self, input_data: dict[int, int]) -> None:
        data = bytearray([0x00] * Constants.PACKET_DATA_LENGTH)
        for pos, val in input_data.items():
            data[pos] = val
        self.send(data)

    def start_effect_command(self) -> None:
        self.send_packet({0x00: Constants.PACKET_HEADER, 0x01: Commands.LED_EFFECT_START_COMMAND})

    def start_effect_page(self) -> None:
        self.send_packet({
            0x00: Constants.PACKET_HEADER,
            0x01: Commands.WRITE_LED_SPECIAL_EFFECT_AREA_COMMAND,
            0x08: Constants.LED_SPECIAL_EFFECT_PACKETS
        })
        self.read()

    def set_customization(self, state: bool) -> None:
        self.send_packet({
            0x00: Constants.PACKET_HEADER,
            0x01: Commands.TURN_ON_CUSTOMIZATION_COMMAND if state else Commands.TURN_OFF_CUSTOMIZATION_COMMAND,
        })
        self.read()

    def end_communication(self) -> None:
        self.send_packet({
            0x00: Constants.PACKET_HEADER,
            0x01: Commands.COMMUNICATION_END_COMMAND,
        })
        self.read()

    def send_leds(self, colors: dict[int | None, RGBColor | None]) -> None:
        color_buffer = bytearray([0x00] * Constants.COLOR_BUF_SIZE)
        for position, color in colors.items():
            if color is None or position is None:
                continue
            color_buffer[position * 4] = POSITION_TO_MEMORY_LOCATION[position]
            color_buffer[position * 4 + 1] = color.red
            color_buffer[position * 4 + 2] = color.green
            color_buffer[position * 4 + 3] = color.blue

        for i in range(int(Constants.COLOR_BUF_SIZE / Constants.PACKET_DATA_LENGTH)):
            partition = memoryview(color_buffer)[
                        i * Constants.PACKET_DATA_LENGTH:(i + 1) * Constants.PACKET_DATA_LENGTH]
            self.send(partition)

    def update_mode(self, active_mode: LightingModes) -> None:
        self.set_customization(True)
        self.start_effect_page()
        # TODO: impl colors
        self.send_packet({
            0x00: active_mode,
            0x08: 1,  # random colors
            0x09: GMK67.MAX_BRIGHTNESS,
            0x10: GMK67.MIN_SPEED,
            0x11: 1,
            0x14: Constants.EFFECT_PAGE_CHECK_CODE_L,
            0x15: Constants.EFFECT_PAGE_CHECK_CODE_H,
        })
        self.read()
        self.end_communication()
        self.start_effect_command()

    def send_direct(self, colors: dict[int, RGBColor | None]) -> None:
        self.send_packet({
            0x0: Constants.PACKET_HEADER,
            0x1: LightingModes.DIRECT_MODE,
            0x8: 0x8,
        })
        self.send_leds(colors)
        self.read()
        self.end_communication()

    def send_custom(self, colors: dict[int, RGBColor | None]) -> None:
        self.set_customization(True)
        self.send_packet({
            0x0: Constants.PACKET_HEADER,
            0x1: LightingModes.CUSTOM_MODE,
            0x8: 0x9
        })

        self.send_leds(colors)
        self.read()
        self.end_communication()

        self.start_effect_command()
        self.set_customization(True)

        self.start_effect_page()
        self.send_packet({
            0x00: LightingModes.LIGHTS_OFF_MODE,
            0x01: 0xFF,
            0x08: 0x01,
            0x09: GMK67.MAX_BRIGHTNESS,
            0x10: GMK67.MIN_SPEED,
            0x14: Constants.EFFECT_PAGE_CHECK_CODE_L,
            0x15: Constants.EFFECT_PAGE_CHECK_CODE_H,
        })
        self.read()
        self.end_communication()
        self.start_effect_command()
