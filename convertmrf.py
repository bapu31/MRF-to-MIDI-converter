from mido import Message, MidiFile, MidiTrack

INPUT_FILE = "convert.MRF"
OUTPUT_FILE = "output.mid"
TIME_SCALE = 4


def extract_events(data):
    events = []

    # Start parsing near track data
    i = data.find(b'TRAK')
    if i == -1:
        i = 0

    current_time = 0

    while i < len(data) - 7:
        # Casio note event pattern
        if (
            0 <= data[i] <= 127 and          # MIDI note
            1 <= data[i + 1] <= 127 and      # velocity
            data[i + 3] in (0x80, 0x81) and  # release marker
            data[i + 5] == 0xFE              # timing marker
        ):
            note = data[i]
            velocity = data[i + 1]

            # Better sustain approximation
            duration = (
                data[i + 2] + data[i + 4] * 2
            ) * TIME_SCALE

            delta = data[i + 6] * TIME_SCALE

            start = current_time
            end = start + duration

            # Polyphonic scheduling
            events.append(("note_on", start, note, velocity))
            events.append(("note_off", end, note, 0))

            current_time += delta
            i += 7
        else:
            i += 1

    return events


with open(INPUT_FILE, "rb") as f:
    data = f.read()

events = extract_events(data)

# Sort events by absolute time
events.sort(key=lambda x: x[1])

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

last_time = 0

for event_type, abs_time, note, velocity in events:
    delta_time = abs_time - last_time
    last_time = abs_time

    track.append(
        Message(
            event_type,
            note=note,
            velocity=velocity,
            time=delta_time
        )
    )

mid.save(OUTPUT_FILE)
print("Saved as", OUTPUT_FILE)