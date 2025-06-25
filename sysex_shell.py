import rtmidi
import asyncio
import os

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
MODES = {
    "session": {"status": 144, "note": 108, "layout": 0x00, "inactive_rgb": (0, 32, 0), "active_rgb": (0, 63, 0)},
    "user1":  {"status": 149, "note": 109, "layout": 0x01, "inactive_rgb": (5, 0, 32), "active_rgb": (10, 0, 63)},
    "user2":  {"status": 157, "note": 110, "layout": 0x02, "inactive_rgb": (32, 0, 32), "active_rgb": (63, 0, 63)},
    "mixer":  {"status": 176, "note": 111, "layout": 0x04, "inactive_rgb": (0, 21, 32), "active_rgb": (0, 42, 63)},
}
MODE_STATUS = {v["status"]: k for k, v in MODES.items()}
MODE_NOTES = {v["note"]: k for k, v in MODES.items()}

COMMANDS = {}
current_mode = None
midi_out = midi_in = None
listener_active = False


def register_command(name):
    def decorator(func):
        COMMANDS[name] = func
        return func
    return decorator


def reconnect():
    global midi_out, midi_in
    midi_out, midi_in = rtmidi.MidiOut(), rtmidi.MidiIn()
    out_ports, in_ports = midi_out.get_ports(), midi_in.get_ports()
    out_idx = next((i for i, n in enumerate(out_ports) if "launchpad" in n.lower()), None)
    in_idx = next((i for i, n in enumerate(in_ports) if "launchpad" in n.lower()), None)
    if out_idx is None or in_idx is None:
        raise RuntimeError("❌ Could not find Launchpad input/output.")
    midi_out.open_port(out_idx)
    midi_in.open_port(in_idx)
    print(f"✅ Connected to: {out_ports[out_idx]} (out), {in_ports[in_idx]} (in)")


def parse_int(val, min_val, max_val, name="value"):
    try:
        v = int(val, 16) if isinstance(val, str) and val.lower().startswith("0x") else int(val)
        if not (min_val <= v <= max_val):
            raise ValueError
        return v
    except Exception:
        print(f"❌ {name} must be {min_val}–{max_val}.")
        return None


def parse_note_list(note_str):
    if not note_str.strip():
        return ALL_NOTES
    try:
        return [int(n.strip()) for n in note_str.split(",") if n.strip()]
    except Exception:
        print("❌ Invalid note number(s).")
        return None


def set_mode(mode_name):
    global current_mode
    if mode_name == current_mode:
        return
    if current_mode:
        midi_out.send_message(HEADER + [0x0B, MODES[current_mode]["note"], 0, 0, 0, 0xF7])
    midi_out.send_message(HEADER + [0x22, MODES[mode_name]["layout"], 0xF7])
    for name, mode in MODES.items():
        note = mode["note"]
        if name == mode_name:
            rgb = mode["active_rgb"]
        elif mode_name in ("session", "mixer"):
            rgb = mode["inactive_rgb"]
        else:
            rgb = (0, 0, 0)
        midi_out.send_message(HEADER + [0x0B, note, *rgb, 0xF7])
    current_mode = mode_name
    return mode_name


def listen_to_input():
    def callback(event, _=None):
        msg = event[0]
        if not msg:
            return
        status, note, velocity = msg[0], msg[1] if len(msg) > 1 else None, msg[2] if len(msg) > 2 else None
        if note in MODE_NOTES and velocity:
            set_mode(MODE_NOTES[note])
        if listener_active:
            print(f"🎵 MIDI Input: [{MODE_STATUS.get(status, f'0x{status:X}')}] {msg}")
    midi_in.set_callback(callback)


async def send_tempo_loop(tempo, max_messages=32):
    interval = 60 / (tempo * 24)
    for _ in range(max_messages):
        midi_out.send_message(HEADER + [0xF8, 0xF7])
        await asyncio.sleep(interval)


@register_command("help")
def cmd_help(_):
    print("""
🎛️  Lighting Commands:
  solid <colour> [notes]            Light notes with RGB (0–63) or palette index (0-127)
  pulse <color_index>               Light all pads with a breathing effect
  flash <color_index>               Light all pads with a flashing effect
  text <color> <speed> <msg>        Display text (color 0–127, speed 0–7)
  clear                             Turn off all pads

🎛️  Utility Commands:
  tempo <bpm> [count]               Send 32 MIDI clocks at BPM (default count=32)
  send/sendraw <hex bytes...>       Send raw SysEx (with or without header)
  mode <name>                       Switch modes (session/user1/user2/mixer)
  reconnect                         Reconnect to the Launchpad
  consoleclear                      Clear the console output
  exit                              Exit the shell

🎛️  Input Commands:
  listenon                          Start listening to MIDI input
  listenoff                         Stop listening to MIDI input
""")


@register_command("exit")
def cmd_exit(_): raise KeyboardInterrupt


@register_command("clear")
def cmd_clear(_):
    midi_out.send_message(HEADER + [0x0E, 0x00, 0xF7])
    print("✅ All pads cleared.")


@register_command("solid")
def cmd_solid(args):
    if not args:
        print("❌ Usage: solid <r> <g> <b> [notes]  or  solid <palette> [notes]")
        return
    if len(args) >= 3:
        r, g, b = (parse_int(args[i], 0, 63, c) for i, c in enumerate(("Red", "Green", "Blue")))
        if None in (r, g, b):
            return
        notes = parse_note_list(args[3]) if len(args) > 3 else ALL_NOTES
        if notes is None:
            return
        for note in notes:
            midi_out.send_message(HEADER + [0x0B, note, r, g, b, 0xF7])
        print(f"✅ Notes set to RGB ({r}, {g}, {b})")
    else:
        color = parse_int(args[0], 0, 127, "Palette")
        if color is None:
            return
        notes = parse_note_list(args[1]) if len(args) > 1 else ALL_NOTES
        if notes is None:
            return
        if notes == ALL_NOTES:
            midi_out.send_message(HEADER + [0x0E, color, 0xF7])
        else:
            for note in notes:
                midi_out.send_message(HEADER + [0x0A, note, color, 0xF7])
        print(f"✅ Notes set to palette color {color}")


def effect_command(effect_type, effect_name):
    @register_command(effect_name)
    def handler(args):
        if not args:
            print(f"❌ Usage: {effect_name} <color_index>")
            return
        color = parse_int(args[0], 0, 127, "Color index")
        if color is None:
            return
        for note in ALL_NOTES:
            midi_out.send_message(HEADER + [effect_type, 0x00, note, color, 0xF7])
        print(f"✅ {effect_name.capitalize()} effect set to color index {color}")


effect_command(0x28, "pulse")
effect_command(0x23, "flash")


@register_command("text")
def cmd_text(args):
    if len(args) < 3:
        print("❌ Usage: text <color (0-127)> <speed (0-7)> <message>")
        return
    color, speed = parse_int(args[0], 0, 127, "Color"), parse_int(args[1], 0, 7, "Speed")
    if color is None or speed is None:
        return
    text_bytes = [ord(c) for c in ' '.join(args[2:])]
    midi_out.send_message(HEADER + [0x14, color, 0x00, speed] + text_bytes + [0xF7])
    print(f"✅ Displaying text: {''.join(chr(b) for b in text_bytes)} color {color} speed {speed}")


@register_command("tempo")
def cmd_tempo(args):
    if not args:
        print("❌ Usage: tempo <bpm (40-240)> [count]")
        return
    bpm = parse_int(args[0], 40, 240, "BPM")
    count = parse_int(args[1], 1, 10000, "Count") if len(args) > 1 else 32
    if bpm is None:
        return

    async def run_tempo():
        await send_tempo_loop(bpm, count)
        print(f"\n✅ Sent {count} tempo messages.")
    try:
        asyncio.run(run_tempo())
    except KeyboardInterrupt:
        pass


@register_command("send")
def cmd_send(args):
    try:
        bytes_list = [int(x, 16) for x in args]
        midi_out.send_message(HEADER + bytes_list + [0xF7])
        print(f"✅ Sent SysEx: {bytes_list}")
    except ValueError:
        print("❌ Invalid hex. Example: send 0B 11 3F 00 00")


@register_command("sendraw")
def cmd_sendraw(args):
    try:
        bytes_list = [int(x, 16) for x in args]
        midi_out.send_message(bytes_list)
        print(f"✅ Sent SysEx: {bytes_list}")
    except ValueError:

        print("❌ Invalid hex. Example: sendraw F0 00 20 29 ... F7")


@register_command("reconnect")
def cmd_reconnect(_):
    try:
        midi_out.close_port()
        midi_in.close_port()
    except Exception:
        pass
    reconnect()
    print("🔁 Reconnected to Launchpad")


@register_command("mode")
def cmd_mode(args):
    if not args or args[0] not in MODES:
        print(f"❌ Usage: mode <{'|'.join(MODES.keys())}>")
        return
    set_mode(args[0])


@register_command("consoleclear")
def cmd_consoleclear(_):
    os.system('cls' if os.name == 'nt' else 'clear')


@register_command("listenon")
def cmd_listenon(_):
    global listener_active
    if listener_active:
        print("👂 Listener already running.")
        return
    listener_active = True
    print("👂 Input listener started.")


@register_command("listenoff")
def cmd_listenoff(_):
    global listener_active
    if listener_active:
        listener_active = False
        print("🛑 Input listener stopped.")
    else:
        print("🛑 Listener is not running.")


def main():
    reconnect()
    set_mode("session")
    listen_to_input()
    print("🎛️  Type 'help' for commands.")
    try:
        while True:
            user_input = input("🧠 > ").strip()
            if not user_input:
                continue
            parts = user_input.split()
            cmd, args = parts[0].lower(), parts[1:]
            if cmd in COMMANDS:
                COMMANDS[cmd](args)
            else:
                print(f"❓ Unknown command: {cmd}. Try 'help'.")
    except KeyboardInterrupt:
        print("👋 Exiting...")
        midi_out.send_message(HEADER + [0x0E, 0x00, 0xF7])
        midi_out.close_port()
        midi_in.close_port()
        cmd_listenoff([])


if __name__ == "__main__":
    main()
