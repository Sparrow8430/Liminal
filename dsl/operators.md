# Operator Reference

## Stack Operators

### PUSH

**Syntax:** `PUSH <symbol>`

**Arity:** 1

**Effect:** Adds symbol to top of stack

**Arguments:**
- `symbol`: String or numeric literal

**Example:**
```
PUSH "alpha"
PUSH "beta"
# Stack: ["alpha", "beta"]
```

**Error Conditions:**
- Stack overflow (exceeds max depth)

---

### INVERT

**Syntax:** `INVERT`

**Arity:** 0

**Effect:** Reverses the entire stack order

**Example:**
```
PUSH "a"
PUSH "b"
PUSH "c"
# Stack before: ["a", "b", "c"]
INVERT
# Stack after: ["c", "b", "a"]
```

**Error Conditions:**
- None (operates on empty stack = no-op)

---

## Binding Operators

### BIND

**Syntax:** `BIND <key> <value>`

**Arity:** 2

**Effect:** Creates an association between key and value in bindings map

**Arguments:**
- `key`: Symbol (string)
- `value`: Symbol (string)

**Example:**
```
BIND "above" "below"
BIND "light" "dark"
# Bindings: {above: below, light: dark}
```

**Semantics:**
- Overwrites existing binding if key already exists
- Does not affect stack
- Bindings persist across phases

**Error Conditions:**
- None in base implementation

---

### RELEASE

**Syntax:** `RELEASE <key>`

**Arity:** 1

**Effect:** Removes binding for specified key

**Arguments:**
- `key`: Symbol (string)

**Example:**
```
BIND "temp" "value"
RELEASE "temp"
# Bindings: {}
```

**Semantics:**
- No-op if key doesn't exist
- Does not affect stack

**Error Conditions:**
- None in base implementation

---

## Control Flow Operators

### GATE

**Syntax:** `GATE <condition>`

**Arity:** 1

**Effect:** Conditional execution - halts current block if condition false

**Arguments:**
- `condition`: Expression that evaluates to boolean

**Supported Conditions:**
- `depth < N` - Stack depth less than N
- `depth > N` - Stack depth greater than N
- `depth == N` - Stack depth equals N
- `bound <key>` - Key exists in bindings
- `unbound <key>` - Key does not exist in bindings

**Example:**
```
SATURATE {
  PUSH "layer"
  GATE depth < 5
}
# Stops adding layers when depth reaches 5
```

**Semantics:**
- Evaluates condition
- If true: continue execution
- If false: exit current block (break)

**Error Conditions:**
- Invalid condition syntax

---

### SATURATE

**Syntax:** `SATURATE { <operations> }`

**Arity:** 1 (block)

**Effect:** Repeats block until fixed point or iteration limit

**Arguments:**
- Block of operations

**Example:**
```
SATURATE {
  PUSH "x"
  GATE depth < 10
}
# Executes until depth reaches 10
```

**Semantics:**
- Executes block repeatedly
- Stops when:
  - Block completes without state change (fixed point)
  - GATE causes early exit
  - Iteration limit reached (1000 by default)

**Fixed Point Detection:**
- Compares stack and bindings before/after each iteration
- If identical, loop terminates

**Error Conditions:**
- Exceeds max iterations (TERM_CYCLE_LIMIT)

---

### HALT

**Syntax:** `HALT`

**Arity:** 0

**Effect:** Terminates program execution immediately

**Example:**
```
BEGIN {
  PUSH "done"
  HALT
}

UNREACHABLE {
  PUSH "never"
}
```

**Semantics:**
- Stops all execution
- Remaining phases are skipped
- Finalizes state and returns

**Error Conditions:**
- None

---

## Observation Operators

### WITNESS

**Syntax:** `WITNESS`

**Arity:** 0

**Effect:** Records current state as checkpoint in trace

**Example:**
```
PUSH "initial"
WITNESS
# Trace records: Stack=["initial"], Bindings={}

PUSH "next"
WITNESS
# Trace records: Stack=["initial", "next"], Bindings={}
```

**Semantics:**
- Does not modify state
- Adds entry to execution trace
- Useful for debugging and analysis

**Error Conditions:**
- None

---

## Operator Precedence

Not applicable - operations execute strictly sequentially.

## Operator Composition

Operators can be composed within phases:

```
BEGIN {
  PUSH "a"
  PUSH "b"
  INVERT
  WITNESS
  BIND "result" "inverted"
}
```

Execution order is always top-to-bottom, left-to-right.

## Type System

### Symbol Type

All stack values and binding keys/values are symbols (strings or numbers treated as strings).

**No type checking** - operators accept any symbol.

### Block Type

Blocks are first-class only for `SATURATE` operator.

## Future Operators (Not Implemented)

These may be added in future versions:

- `DUP` - Duplicate top of stack
- `SWAP` - Swap top two stack elements
- `DROP` - Remove top of stack
- `PEEK` - Read without removing
- `MERGE` - Combine bindings
- `CLEAR` - Empty stack or bindings

## Operator Behavior Summary

| Operator | Modifies Stack | Modifies Bindings | Control Flow |
|----------|----------------|-------------------|--------------|
| PUSH | Yes | No | No |
| INVERT | Yes | No | No |
| BIND | No | Yes | No |
| RELEASE | No | Yes | No |
| GATE | No | No | Yes (conditional) |
| SATURATE | Depends on block | Depends on block | Yes (loop) |
| WITNESS | No | No | No |
| HALT | No | No | Yes (exit) |

## Implementation Notes

### State Isolation

Operators cannot:
- Access filesystem
- Make network requests
- Generate random values
- Access system time
- Read environment variables

All state is explicit and contained within:
- Stack (list of symbols)
- Bindings (map of symbol → symbol)
- Phase counter
- Operation counter

### Determinism Guarantee

Given identical input program and VM configuration:
- Execution always produces identical output
- Same number of operations
- Same final state
- Same trace checkpoints

This is enforced by:
- No external dependencies
- No non-deterministic operators
- Fixed iteration limits
- Explicit state management
