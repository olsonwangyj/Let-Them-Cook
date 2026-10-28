# Hand events for the game (`HAND_EVENT`)

For Jie Ling, from Communications (olsonwangyj). Written on 2026-10-28.

**Status:** built and tested on the laptop and in a Linux Swift build, then run with both test
boards against a service on the laptop. **Deployed on the Ultra96 on 2026-10-28 at 22:21 (+08:00)**,
and run through it with both test boards (with the synthetic test model, so the gestures mean
nothing). That night it was also tested on macOS and built for iOS on the owner's Mac: your
export `SinkTest_V1 2`, rebuilt with it, defines both functions below and is installed on the
owner's iPhone (as `com.CG4002.unityTutorial.olson`; no Connect yet); your code does not call
them yet. Just after midnight on 2026-10-29 the comms test app on the same iPhone, built with the
same CommsNative, subscribed to the Ultra96 with hand events and was sent every hand event and
result of a 5-minute run with two test boards. The full specification is the section "Hand events (`HAND_EVENT`, opt-in)" of
[co-protocol-v3.md](co-protocol-v3.md); this page is what the game needs.

## What changes for the game

Nothing, unless the game uses the two new functions below.

`CommsNextResult` keeps working exactly as now. It delivers one `GESTURE_RESULT` per pulse, state
start, state refresh or idle, with `device_id` naming the hand.

What is new is structured per-hand events. The game can see when an ongoing action (CHOP, WASH,
POURING) starts and ends, and each hand's current state, instead of inferring them from repeated
results.

## Hands

- `device_id` 1 is the LEFT hand and 2 is the RIGHT hand.
- The two hands are independent: each has its own events, its own sequence numbers and its own
  state, and both can be doing something at the same time.

## The two functions (CommsNative, iOS build only)

```c
int32_t CommsHandState(char* buffer, int32_t capacity);
int32_t CommsNextHandEvent(char* buffer, int32_t capacity);
```

In C#, as for `CommsNextResult` and inside the same `#if UNITY_IOS && !UNITY_EDITOR`:

```csharp
[DllImport("__Internal")] static extern int CommsHandState(byte[] buffer, int capacity);
[DllImport("__Internal")] static extern int CommsNextHandEvent(byte[] buffer, int capacity);
```

Both work like `CommsNextResult`:
- they write compact UTF-8 JSON plus a terminating 0 and return the byte count;
- they return −(bytes + 1) when the buffer is null or too small, and then write nothing;
- they never block, so you can call them every frame on the main thread.

A 1024-byte buffer is always enough.

### `CommsHandState`: both hands, now

This call always returns a snapshot; it never returns 0. Example:

```json
{"worker_epoch":"006cd40f2e970c1f106915264e6d84e8","invalid":0,"hands":[
 {"device_id":1,"gesture":null,"state_id":null,"expires_in_ms":null,"last_pulse_gesture":"THROW","last_pulse_event_id":"006cd40f2e970c1f106915264e6d84e8:1:2","accepted":2,"duplicate":0,"ignored":0},
 {"device_id":2,"gesture":"WASH","state_id":"006cd40f2e970c1f106915264e6d84e8:2:1","expires_in_ms":812,"last_pulse_gesture":null,"last_pulse_event_id":null,"accepted":2,"duplicate":0,"ignored":0}]}
```

- **`gesture`:** the hand's ongoing action (`CHOP`, `WASH`, `POURING`), or null when it has none.
  This is the field to drive a continuous animation from.
- **`expires_in_ms`:** how long the state lasts without another refresh.
- **`last_pulse_gesture`, `last_pulse_event_id`:** the latest one-shot action of that hand.
- **`accepted`, `duplicate`, `ignored`:** counters for logs.
- **`invalid`:** hand events that were malformed and dropped.

The phone ends a state by itself when its lease runs out, so `gesture` turns null even if no end
message arrives.

### `CommsNextHandEvent`: each event once

This call returns the next hand event, or 0 when none waits. Each event comes out once and in
order. Duplicates, late events and events that name an unknown state are filtered out before they
reach the queue. At most 64 events wait, and an event waits at most 2 s.

## The event (15 fields)

```json
{"v":4,"type":"HAND_EVENT","event_format":1,"session_id":"ltc-comms","worker_epoch":"006cd40f2e970c1f106915264e6d84e8","device_id":2,"event_seq":1,"event_id":"006cd40f2e970c1f106915264e6d84e8:2:1","kind":"state_start","gesture":"WASH","confidence":0.509,"source":{"boot_id":3866574055,"seq":105192,"uptime_ms":68404947},"state_id":"006cd40f2e970c1f106915264e6d84e8:2:1","lease_ms":1000,"reason":"confirmed"}
```

| Field | Meaning for the game |
|---|---|
| `device_id` | 1 LEFT, 2 RIGHT |
| `kind` | `pulse`, `state_start`, `state_refresh`, `state_end`, `idle` or `reset` (next table) |
| `gesture` | `PICKUP`, `DROP` or `THROW` for a pulse; `CHOP`, `WASH` or `POURING` for a state; `IDLE` for idle; null for reset |
| `confidence` | the model's confidence, 0 to 1; null for `state_end` and `reset` |
| `event_id` | unique per event; a game that keeps its own list can de-duplicate by it |
| `state_id` | which state a start, refresh or end belongs to (a start's `state_id` is its own `event_id`) |
| `lease_ms` | on start and refresh, how long the state lasts without another refresh (1000 ms); 0 otherwise |
| `reason` | `confirmed` for model predictions; for an end or reset, why it ended (`confirmed_transition`, `prediction_timeout`, `source_reset`, `connection_reset`, `worker_disconnect`, `manual_reset`) |
| `worker_epoch`, `event_seq`, `source`, `v`, `type`, `event_format`, `session_id` | bookkeeping; the game can ignore them |

## What to do with each kind

| `kind` | What it means | What the game does |
|---|---|---|
| `pulse` | A one-shot action: PICKUP, DROP or THROW | Do the action once. The game decides whether it is valid at that moment. |
| `state_start` | An ongoing action begins: CHOP, WASH or POURING | Start the continuous action for that hand. |
| `state_refresh` | The hand is still doing it (about every 0.2 s) | Keep going. |
| `state_end` | The ongoing action stopped | Stop it. A change from CHOP to POURING arrives as `state_end` CHOP, then `state_start` POURING, sometimes both from one sensor sample. |
| `idle` | The model confirmed IDLE | That hand does nothing. |
| `reset` | The hand's state is reset (not a prediction) | Stop whatever that hand was doing. |

- **No refresh for `lease_ms`:** the action is over, end message or not. The phone has already
  ended it in `CommsHandState`. An end that arrives after that never comes out of
  `CommsNextHandEvent`.
- **A glove restart or reconnect:** that hand alone is reset. Its state ends, and the next events
  come from the glove's new connection.

## Compared with `GESTURE_RESULT`

| | `GESTURE_RESULT` (now) | `HAND_EVENT` (new) |
|---|---|---|
| A one-shot action | one result | one `pulse` |
| An ongoing action | the same result about every 0.2 s, no end message | `state_start`, `state_refresh`es, then `state_end` (or the lease runs out) |
| A change of action | the next label just starts arriving | `state_end` of the old state, then `state_start` of the new one |
| Each hand's state | the game has to infer it | `CommsHandState` |

## What has to happen before it works on the phone

1. **Ultra96 service:** ~~the service on the Ultra96 is redeployed with this version~~ done on
   2026-10-28 at 22:21.
2. **CommsNative build:** done on 2026-10-28 for your export `SinkTest_V1 2` (its `UnityFramework`
   defines `CommsHandState` and `CommsNextHandEvent`). Each later export of yours is rebuilt the
   same way on the owner's Mac with `build_game_ios.sh`, which refuses a build without them.
3. **Game code:** the game calls the new functions. That is a change in your `CommsBridge.cs`;
   Communications does not edit it.

**Against an older service** (such as the Ultra96's before 2026-10-28 22:21): an app built with the
new CommsNative still works. It asks for hand events, is refused, and subscribes again the old way, so its status shows
`no hand events from this service; retrying with subscription version 1`. `CommsNextResult` keeps
delivering as before.
