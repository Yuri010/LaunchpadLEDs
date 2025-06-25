# LaunchpadLEDs

A collection of Python scripts for controlling a Novation Launchpad MK2 via MIDI System Exclusive (SysEx) messages.  
This project lets you experiment with lighting, text, and effects on your Launchpad, and includes an interactive shell for live control.

---

## Features

- **Interactive Shell**: Run commands to control lights, display text, switch modes, and more ([sysex_shell.py](sysex_shell.py)).
- **Lighting Effects**: Set solid colors, pulse, flash, and clear pads.
- **Text Display**: Scroll custom text across the Launchpad.
- **Tempo Control**: Send MIDI clock messages to adjust effect tempo.
- **Raw SysEx**: Send custom SysEx messages for advanced use.
- **Mode Switching**: Emulate Ableton-style mode switching with visual feedback.
- **Input Listener**: Monitor and display incoming MIDI messages.

---

## Requirements

- Python 3.7+
- [python-rtmidi](https://pypi.org/project/python-rtmidi/)

Install dependencies:
```sh
pip install python-rtmidi
```

---

## File Tree

```
.
├── sysex_shell.py              # Main interactive shell for Launchpad control
├── misc/
│   ├── lights.py               # Simple script for lighting pads
│   ├── lights_bpm.py           # Lighting with tempo/BPM control
│   ├── text.py                 # Script for scrolling text
│   ├── launchpad_user1_drumrack.syx   # SysEx dump to switch to drumrack layout
│   ├── launchpad_user2_session.syx    # SysEx dump to switch to session layout
│   └── palette.png             # Color palette reference
├── README.md
└── .pylintrc
```

---

## Usage

### 1. Launch the Interactive Shell

```sh
python sysex_shell.py
```

Type `help` in the shell for a list of commands.

### 2. Run Example Scripts

- Lighting pads:  
  ```sh
  python misc/lights.py
  ```
- Lighting with BPM/tempo:  
  ```sh
  python misc/lights_bpm.py
  ```
- Scrolling text:  
  ```sh
  python misc/text.py
  ```

---

## SysEx Reference

The Launchpad MK2 uses SysEx messages with the following header:
```py
0xF0, 0x00, 0x20, 0x29, 0x02, 0x18,  # Header
# ...message...
0xF7  # End of SysEx
```

Common lighting commands:
```py
0x0A, LED, Colour             # Palette color (0-127)
0x0B, LED, R, G, B            # RGB color (0-63 each)
0x0E, Colour                  # All LEDs
0x23, 0, LED, Colour          # Flash effect
0x28, 0, LED, Colour          # Pulse effect
0x14, Colour, Loop, Speed, ...Text...  # Scroll text
```
See [Novation Launchpad MK2 Programmer's Reference](https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Launchpad%20MK2%20Programmers%20Reference%20Manual%20v1.03.pdf) for more.

---

## Example Shell Commands

- `solid 63 0 63` — Set all pads to magenta (RGB)
- `solid 5` — Set all pads to palette color 5
- `pulse 10` — Pulse all pads with palette color 10
- `flash 20` — Flash all pads with palette color 20
- `text 15 3 Hello!` — Scroll "Hello!" in color 15 at speed 3
- `clear` — Turn off all pads
- `mode user1` — Switch to User 1 mode
- `tempo 120` — Send MIDI clock at 120 BPM

---

## License

This project is provided as-is for hobby and educational use.

---

## Credits

- [Novation Launchpad MK2 Programmer's Reference Manual](https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Launchpad%20MK2%20Programmers%20Reference%20Manual%20v1.03.pdf)
- Inspired by the Ableton workflow and Launchpad community.

---