# Controls Reference

## Keyboard Layout (ISO Standard — default)

The default keyboard scheme approximates the ISO two-joystick layout
used in real excavators. Left-hand keys control the superstructure;
right-hand keys control the arm.

```
┌─────────────────────────────────────────────────────────┐
│  LEFT JOYSTICK (superstructure)  │  RIGHT JOYSTICK (arm) │
│                                  │                       │
│     Q (swing L)  W (boom ↑)      │   boom ↑   arm ext   │
│     A (swing)    S (boom ↓)      │   I        O          │
│     (arm handled on right)       │   K (boom↓) L (ret)  │
│                                  │   U (bucket curl)     │
│  ─────────────────────────────── │   J (bucket dump)     │
│  TRACKS (arrow keys)             │                       │
│     ↑  Forward                   │                       │
│     ↓  Backward                  │                       │
│     ←  Turn left                 │                       │
│     →  Turn right                │                       │
└─────────────────────────────────────────────────────────┘
```

### Detailed Binding Table

| Action | Primary Key | Gamepad Axis |
|--------|-------------|--------------|
| Boom up | W | Right stick Y− |
| Boom down | S | Right stick Y+ |
| Arm extend | A | Left stick X− |
| Arm retract | D | Left stick X+ |
| Bucket curl | Q | Right stick X− |
| Bucket dump | E | Right stick X+ |
| Swing left | J | Left stick X− |
| Swing right | L | Left stick X+ |
| Track forward | ↑ | Left trigger |
| Track backward | ↓ | Right trigger |
| Track turn left | ← | Left stick X− |
| Track turn right | → | Left stick X+ |

---

## Gamepad Layout (XInput / DualShock)

```
Left Stick:   Swing (X) + Boom (Y)
Right Stick:  Arm (X) + Bucket (Y)
L2 / LT:     Track forward
R2 / RT:     Track backward
L1 / LB:     Track turn left
R1 / RB:     Track turn right
```

This matches the **ISO pattern** (most common outside North America).
The **SAE pattern** swaps left/right stick assignments — configurable
in Godot Project Settings → Input Map.

---

## Excavator Operating Tips

1. **Dig cycle**: Lower boom (S) → extend arm (D) → curl bucket (Q) to fill
2. **Swing to dump**: Release dig inputs → swing (J/L) to position over truck
3. **Dump**: Dump bucket (E) while holding swing position
4. **Rough digging**: Use boom + arm together for faster material displacement
5. **Fine positioning**: Use arm only for precise scraping

## Physics Feel Notes

- Bucket load increases resistance — joints move slower when full
- Hard materials (rock > clay > dirt > sand) require more input to carve
- Particles slide off steep piles naturally; pile angle matches material
- Settled particles re-solidify (return to voxel terrain) after ~2 seconds at rest
