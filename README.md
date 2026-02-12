# liminal-vm

A deterministic virtual machine for executing symbolic state-transition scripts.

## What This Is

A stack-based VM that processes `.lmn` programs through defined execution phases. Each program is a sequence of symbolic operators that transform internal state according to strict rules.

Think of it as a Forth-like language for state machines, but the state is conceptual rather than computational.

## Architecture

```
Input (.lmn script)
    ↓
Parser (validates grammar)
    ↓
VM (executes phases)
    ↓
Output (final state + trace)
```

## Installation

```bash
# Using Python implementation
python3 -m pip install -r requirements.txt

# Run a program
python3 src/liminal.py examples/inversion.lmn --trace
```

## Quick Start

```bash
# Validate a program
python3 src/liminal.py check examples/inversion.lmn

# Execute with trace output
python3 src/liminal.py run examples/inversion.lmn --trace

# Execute with custom limits
python3 src/liminal.py run examples/saturation.lmn --max-ops 50000 --max-stack 128
```

## Repository Structure

- `/dsl` - Language specification
  - `grammar.md` - Formal grammar definition
  - `operators.md` - Operator reference
  - `termination.md` - Termination conditions
- `/vm` - Execution engine design
  - `execution_phases.md` - VM phase documentation
  - `fail_safes.md` - Safety mechanisms
- `/examples` - Sample `.lmn` programs
- `/src` - Python implementation
- `/tests` - Test suite

## Language Overview

Programs are composed of phases containing operations:

```
PHASE_NAME {
  OPERATOR arg1 arg2
  OPERATOR arg1
}
```

### Core Operators

- `PUSH <symbol>` - Add symbol to stack
- `INVERT` - Reverse stack order
- `BIND <key> <value>` - Create association
- `RELEASE <key>` - Remove binding
- `GATE <condition>` - Conditional branch
- `SATURATE <block>` - Repeat until fixed point
- `WITNESS` - Mark state checkpoint
- `HALT` - Terminate execution

See `/dsl/operators.md` for complete reference.

## Example Program

```
BEGIN {
  PUSH "above"
  PUSH "below"
  WITNESS
}

TRANSFORM {
  INVERT
  WITNESS
}

RESOLVE {
  BIND "above" "below"
  HALT
}
```

## Design Principles

1. **No I/O during execution** - Programs cannot read files or network
2. **Deterministic semantics** - Same input always produces same output
3. **Explicit state** - All state changes visible in trace
4. **Bounded resources** - Hard limits prevent runaway execution

## Non-Goals

This is **not**:
- A practical programming language
- A theorem prover
- A simulation framework
- A tool for any specific domain

It is:
- A formally specified state machine
- An exercise in language design
- A sandbox for exploring symbolic computation

## Contributing

Contributions should focus on:
- Clearer operator semantics
- Additional fail-safe mechanisms
- Optimization of VM core
- Expanded test coverage

Not welcome:
- Operators with side effects
- Non-deterministic features
- Claims about practical applications

## License

MIT - Use at your own risk.

---

**Note:** This VM executes symbolic transformations. What those transformations *mean* is outside its scope. The machine is value-neutral by design.
