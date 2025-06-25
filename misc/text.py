import rtmidi

HEADER = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x18]


def setup_midi():
    midi_out = rtmidi.MidiOut()
    ports = midi_out.get_ports()
    for idx, p in enumerate(ports):
        if "Launchpad" in p:
            midi_out.open_port(idx)
            return midi_out
    raise RuntimeError("Launchpad not found!")


def get_int_input(prompt, min_val, max_val):
    try:
        value = int(input(prompt).strip())
        if min_val <= value <= max_val:
            return value
    except ValueError:
        pass
    print(f"❌ Value must be {min_val}–{max_val}.")
    return None


def send_rgb(midi_out, color, loop, speed_and_text):
    sysex = HEADER + [0x14, color, loop] + speed_and_text + [0xF7]
    midi_out.send_message(sysex)


def main():
    midi_out = setup_midi()
    color = get_int_input("Enter color (0–127): ", 0, 127)
    if color is None:
        return

    loop = 0x01 if input("Loop text? (y/n): ").strip().lower() == 'y' else 0x00
    speed = get_int_input("Enter speed (0–7): ", 0, 7)
    if speed is None:
        return

    text_str = input("Enter text to display: ")
    speed_and_text = [speed] + [ord(c) for c in text_str]

    send_rgb(midi_out, color, loop, speed_and_text)
    print("Press Ctrl+C to quit.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        midi_out.send_message(HEADER + [0x14, 0x00, 0x00, 0xF7])
    finally:
        midi_out.close_port()


if __name__ == "__main__":
    main()