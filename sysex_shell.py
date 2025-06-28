import asyncio
import os
from launchpad import Launchpad, ALL_NOTES

COMMANDS = {}


def register_command(name):
    def decorator(func):
        COMMANDS[name] = func
        return func
    return decorator


def parse_int(val, min_val, max_val, name="value"):
    try:
        v = int(val, 16) if isinstance(val, str) and val.lower().startswith("0x") else int(val)
        if not min_val <= v <= max_val:
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


@register_command("help")
def cmd_help(_lp, _):
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
def cmd_exit(lp, _):
    raise KeyboardInterrupt


@register_command("clear")
def cmd_clear(lp, _):
    lp.clear()
    print("✅ All pads cleared.")


@register_command("solid")
def cmd_solid(lp, args):
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
        lp.solid(r, g, b, notes)
        print(f"✅ Notes set to RGB ({r}, {g}, {b})")
    else:
        color = parse_int(args[0], 0, 127, "Palette")
        if color is None:
            return
        notes = parse_note_list(args[1]) if len(args) > 1 else ALL_NOTES
        if notes is None:
            return
        lp.palette(color, notes)
        print(f"✅ Notes set to palette color {color}")


def effect_command(effect_type, effect_name):
    @register_command(effect_name)
    def handler(lp, args):
        if not args:
            print(f"❌ Usage: {effect_name} <color_index>")
            return
        color = parse_int(args[0], 0, 127, "Color index")
        if color is None:
            return
        lp.effect(effect_type, color)
        print(f"✅ {effect_name.capitalize()} effect set to color index {color}")


effect_command(0x28, "pulse")
effect_command(0x23, "flash")


@register_command("text")
def cmd_text(lp, args):
    if len(args) < 3:
        print("❌ Usage: text <color (0-127)> <speed (0-7)> <message>")
        return
    color, speed = parse_int(args[0], 0, 127, "Color"), parse_int(args[1], 0, 7, "Speed")
    if color is None or speed is None:
        return
    message = ' '.join(args[2:])
    lp.text(color, speed, message)
    print(f"✅ Displaying text: {message} color {color} speed {speed}")


@register_command("tempo")
def cmd_tempo(lp, args):
    if not args:
        print("❌ Usage: tempo <bpm (40-240)> [count]")
        return
    bpm = parse_int(args[0], 40, 240, "BPM")
    count = parse_int(args[1], 1, 10000, "Count") if len(args) > 1 else 32
    if bpm is None:
        return

    async def run_tempo():
        await lp.send_tempo_loop(bpm, count)
        print(f"\n✅ Sent {count} tempo messages.")
    try:
        asyncio.run(run_tempo())
    except KeyboardInterrupt:
        pass


@register_command("send")
def cmd_send(lp, args):
    try:
        bytes_list = [int(x, 16) for x in args]
        lp.send_sysex(bytes_list)
        print(f"✅ Sent SysEx: {bytes_list}")
    except ValueError:
        print("❌ Invalid hex. Example: send 0B 11 3F 00 00")


@register_command("sendraw")
def cmd_sendraw(lp, args):
    try:
        bytes_list = [int(x, 16) for x in args]
        lp.send_raw(bytes_list)
        print(f"✅ Sent SysEx: {bytes_list}")
    except ValueError:
        print("❌ Invalid hex. Example: sendraw F0 00 20 29 ... F7")


@register_command("reconnect")
def cmd_reconnect(lp, _):
    lp.reconnect()
    print("🔁 Reconnected to Launchpad")


@register_command("mode")
def cmd_mode(lp, args):
    lp.set_mode(args[0])


@register_command("consoleclear")
def cmd_consoleclear(_lp, _):
    os.system('cls' if os.name == 'nt' else 'clear')


@register_command("listenon")
def cmd_listenon(lp, _):
    if lp.listener_active:
        print("👂 Listener already running.")
        return
    lp.listener_active = True
    print("👂 Input listener started.")


@register_command("listenoff")
def cmd_listenoff(lp, _):
    if lp.listener_active:
        lp.listener_active = False
        print("🛑 Input listener stopped.")
    else:
        print("🛑 Listener is not running.")


def main():
    lp = Launchpad()
    lp.set_mode("session")
    lp.listen_to_input()
    print("🎛️  Type 'help' for commands.")
    try:
        while True:
            user_input = input("🧠 > ").strip()
            if not user_input:
                continue
            parts = user_input.split()
            cmd, args = parts[0].lower(), parts[1:]
            if cmd in COMMANDS:
                COMMANDS[cmd](lp, args)
            else:
                print(f"❓ Unknown command: {cmd}. Try 'help'.")
    except KeyboardInterrupt:
        lp.disconnect()
        print("👋 Exiting...")


if __name__ == "__main__":
    main()
