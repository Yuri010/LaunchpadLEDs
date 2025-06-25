import asyncio
import rtmidi

HEADER = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x18]

ALL_NOTES = [
    104, 105, 106, 107, 108, 109, 110, 111,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    71, 72, 73, 74, 75, 76, 77, 78, 79,
    61, 62, 63, 64, 65, 66, 67, 68, 69,
    51, 52, 53, 54, 55, 56, 57, 58, 59,
    41, 42, 43, 44, 45, 46, 47, 48, 49,
    31, 32, 33, 34, 35, 36, 37, 38, 39,
    21, 22, 23, 24, 25, 26, 27, 28, 29,
    11, 12, 13, 14, 15, 16, 17, 18, 19,
]

MAX_TEMPO_MESSAGES = 32


def setup_midi():
    midi_out = rtmidi.MidiOut()
    ports = midi_out.get_ports()
    for idx, p in enumerate(ports):
        if "Launchpad" in p:
            midi_out.open_port(idx)
            return midi_out
    raise RuntimeError("Launchpad not found!")


def send_palette_all(midi_out, color):
    for note in ALL_NOTES:
        midi_out.send_message(HEADER + [0x28, 0, note, color, 0xF7])


async def change_tempo(midi_out, tempo, max_messages=None):
    interval = 60 / (tempo * 24)
    for count in range(max_messages or float('inf')):
        midi_out.send_message(HEADER + [0xF8, 0xF7])
        await asyncio.sleep(interval)


def main():
    midi_out = setup_midi()
    color_input = input("Enter colour value (0-127): ").strip()
    try:
        color = int(color_input, 16) if color_input.lower().startswith("0x") else int(color_input)
        if not 0 <= color <= 127:
            raise ValueError
    except ValueError:
        print("❌ Invalid palette value. Enter a number 0-127 or hex 0x00-0x7F.")
        midi_out.close_port()
        return

    send_palette_all(midi_out, color)

    tempo_input = input("Enter tempo in BPM (40-240): ")
    try:
        tempo = int(tempo_input)
        if not 40 <= tempo <= 240:
            raise ValueError
    except ValueError:
        print("❌ Invalid tempo. Enter a number between 40 and 240.")
        midi_out.close_port()
        return

    async def run_tempo_loop():
        try:
            await change_tempo(midi_out, tempo, MAX_TEMPO_MESSAGES)
            print(f"\n✅ Sent {MAX_TEMPO_MESSAGES} tempo messages. Press Enter to exit and shut down the device.")
            await asyncio.get_event_loop().run_in_executor(None, input)
        except KeyboardInterrupt:
            print("👋 Exiting...")
        finally:
            midi_out.send_message(HEADER + [0x0E, 0x00, 0xF7])
            midi_out.close_port()

    try:
        asyncio.run(run_tempo_loop())
    except KeyboardInterrupt:
        print("👋 Exiting...")
        midi_out.send_message(HEADER + [0x0E, 0x00, 0xF7])
        midi_out.close_port()


if __name__ == "__main__":
    main()
