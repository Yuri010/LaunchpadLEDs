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


def setup_midi():
    midi_out = rtmidi.MidiOut()
    ports = midi_out.get_ports()
    for idx, p in enumerate(ports):
        if "Launchpad" in p:
            midi_out.open_port(idx)
            return midi_out
    raise RuntimeError("Launchpad not found!")


def send_rgb(midi_out, note, r, g, b):
    midi_out.send_message(HEADER + [0x0B, note, r, g, b, 0xF7])


def send_palette(midi_out, note, color):
    if note:
        midi_out.send_message(HEADER + [0x0A, note, color, 0xF7])
    else:
        midi_out.send_message(HEADER + [0x0E, color, 0xF7])


def main():
    midi_out = setup_midi()
    note_input = input("Enter note number(s) to light (comma separated, blank for all): ").strip()
    color_input = input("Enter RGB values (e.g. 63 0 63) or a single palette value (0-127: ").strip()

    rgb_parts = color_input.split()
    use_rgb = False
    if len(rgb_parts) == 3:
        try:
            r, g, b = map(int, rgb_parts)
            if all(0 <= v <= 63 for v in (r, g, b)):
                use_rgb = True
            else:
                raise ValueError
        except ValueError:
            print("❌ Invalid RGB values. Please enter three numbers between 0 and 63.")
            midi_out.close_port()
            return
    else:
        try:
            color = int(color_input, 16) if color_input.lower().startswith("0x") else int(color_input)
            if not (0 <= color <= 127):
                raise ValueError
        except ValueError:
            print("❌ Invalid palette value. Enter a number 0-127 or hex 0x00-0x7F.")
            midi_out.close_port()
            return

    if not note_input:
        notes = ALL_NOTES
    else:
        try:
            notes = [int(n) for n in note_input.split(",") if n.strip()]
        except ValueError:
            print("❌ Invalid note number(s).")
            midi_out.close_port()
            return

    if use_rgb:
        for note in notes:
            send_rgb(midi_out, note, r, g, b)
    else:
        if notes == ALL_NOTES:
            send_palette(midi_out, 0, color)
        else:
            for note in notes:
                send_palette(midi_out, note, color)

    midi_out.close_port()


if __name__ == "__main__":
    main()