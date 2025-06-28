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
MODES = {
    "session": {"status": 144, "note": 108, "layout": 0x00, "inactive_rgb": (0, 32, 0), "active_rgb": (0, 63, 0)},
    "user1":  {"status": 149, "note": 109, "layout": 0x01, "inactive_rgb": (5, 0, 32), "active_rgb": (10, 0, 63)},
    "user2":  {"status": 157, "note": 110, "layout": 0x02, "inactive_rgb": (32, 0, 32), "active_rgb": (63, 0, 63)},
    "mixer":  {"status": 176, "note": 111, "layout": 0x04, "inactive_rgb": (0, 21, 32), "active_rgb": (0, 42, 63)},
}
MODE_STATUS = {v["status"]: k for k, v in MODES.items()}
MODE_NOTES = {v["note"]: k for k, v in MODES.items()}


class Launchpad:
    def __init__(self):
        self.midi_out = None
        self.midi_in = None
        self.current_mode = None
        self.listener_active = False
        self.reconnect()

    def reconnect(self):
        self.disconnect()
        self.midi_out, self.midi_in = rtmidi.MidiOut(), rtmidi.MidiIn()
        out_ports, in_ports = self.midi_out.get_ports(), self.midi_in.get_ports()
        out_idx = next((i for i, n in enumerate(out_ports) if "launchpad" in n.lower()), None)
        in_idx = next((i for i, n in enumerate(in_ports) if "launchpad" in n.lower()), None)
        if out_idx is None or in_idx is None:
            raise RuntimeError("❌ Could not find Launchpad input/output.")
        self.midi_out.open_port(out_idx)
        self.midi_in.open_port(in_idx)
        print(f"✅ Connected to: {out_ports[out_idx]} (out), {in_ports[in_idx]} (in)")

    def disconnect(self):
        if self.midi_out:
            self.clear()
            try:
                self.midi_out.close_port()
            except Exception as e:
                print(f"❌ Error closing MIDI out port: {e}")
        if self.midi_in:
            try:
                self.midi_in.close_port()
            except Exception as e:
                print(f"❌ Error closing MIDI in port: {e}")

    def set_mode(self, mode_name):
        if not mode_name or mode_name not in MODES:
            print(f"❌ Usage: mode <{'|'.join(MODES.keys())}>")
            return
        if mode_name == self.current_mode:
            return
        if self.current_mode:
            self.midi_out.send_message(HEADER + [0x0B, MODES[self.current_mode]["note"], 0, 0, 0, 0xF7])
        self.midi_out.send_message(HEADER + [0x22, MODES[mode_name]["layout"], 0xF7])
        for name, mode in MODES.items():
            note = mode["note"]
            if name == mode_name:
                rgb = mode["active_rgb"]
            elif mode_name in ("session", "mixer"):
                rgb = mode["inactive_rgb"]
            else:
                rgb = (0, 0, 0)
            self.midi_out.send_message(HEADER + [0x0B, note, *rgb, 0xF7])
        self.current_mode = mode_name
        return mode_name

    def clear(self):
        self.midi_out.send_message(HEADER + [0x0E, 0x00, 0xF7])

    def solid(self, r, g, b, notes=ALL_NOTES):
        for note in notes:
            self.midi_out.send_message(HEADER + [0x0B, note, r, g, b, 0xF7])

    def palette(self, color, notes=ALL_NOTES):
        if notes == ALL_NOTES:
            self.midi_out.send_message(HEADER + [0x0E, color, 0xF7])
        else:
            for note in notes:
                self.midi_out.send_message(HEADER + [0x0A, note, color, 0xF7])

    def effect(self, effect_type, color):
        for note in ALL_NOTES:
            self.midi_out.send_message(HEADER + [effect_type, 0x00, note, color, 0xF7])

    def text(self, color, speed, message):
        text_bytes = [ord(c) for c in message]
        self.midi_out.send_message(HEADER + [0x14, color, 0x00, speed] + text_bytes + [0xF7])

    def send_sysex(self, bytes_list):
        self.midi_out.send_message(HEADER + bytes_list + [0xF7])

    def send_raw(self, bytes_list):
        self.midi_out.send_message(bytes_list)

    def listen_to_input(self):
        def callback(event, _=None):
            msg = event[0]
            if not msg:
                return
            status, note, velocity = msg[0], msg[1] if len(msg) > 1 else None, msg[2] if len(msg) > 2 else None
            if note in MODE_NOTES and velocity:
                self.set_mode(MODE_NOTES[note])
            if self.listener_active:
                print(f"🎵 MIDI Input: [{MODE_STATUS.get(status, f'0x{status:X}')}] {msg}")
        self.midi_in.set_callback(callback)

    async def send_tempo_loop(self, tempo, max_messages=32):
        interval = 60 / (tempo * 24)
        for _ in range(max_messages):
            self.midi_out.send_message(HEADER + [0xF8, 0xF7])
            await asyncio.sleep(interval)
