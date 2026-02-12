# Quick Start Guide

## Installation

No installation needed - liminal-vm is a standalone Python script with no dependencies.

Requirements:
- Python 3.8 or higher

## First Run

```bash
# Make the script executable
chmod +x src/liminal.py

# Run an example program
python3 src/liminal.py run examples/inversion.lmn --trace
```

## Basic Usage

### 1. Validate a Program

```bash
python3 src/liminal.py check examples/saturation.lmn
```

Output:
```
✓ examples/saturation.lmn is valid
```

### 2. Execute a Program

```bash
python3 src/liminal.py run examples/inversion.lmn
```

Output:
```
============================================================
Status: HALTED
============================================================
Phases executed: 3
Operations executed: 6
============================================================

Final State:
  Stack depth: 2
  Stack: ['below', 'above']
  Bindings: {'above': 'below'}
============================================================
```

### 3. Execute with Trace

```bash
python3 src/liminal.py run examples/saturation.lmn --trace
```

Shows execution checkpoints at each WITNESS operation.

### 4. Custom Resource Limits

```bash
python3 src/liminal.py run examples/comprehensive.lmn \
  --max-ops 50000 \
  --max-stack 128 \
  --max-saturate 500
```

### 5. JSON Output

```bash
python3 src/liminal.py run examples/binding.lmn --json > output.json
```

## Example Programs

### inversion.lmn
Demonstrates PUSH, INVERT, BIND, and WITNESS operations.

### saturation.lmn
Shows SATURATE loop with GATE condition.

### binding.lmn
Illustrates BIND/RELEASE and conditional GATE checks.

### fixed_point.lmn
Demonstrates SATURATE fixed point detection.

### comprehensive.lmn
Uses all available operators in a complex flow.

## Writing Your First Program

Create `hello.lmn`:

```
BEGIN {
  PUSH "hello"
  PUSH "world"
  WITNESS
}

FINISH {
  INVERT
  WITNESS
  HALT
}
```

Run it:

```bash
python3 src/liminal.py run hello.lmn --trace
```

## Common Patterns

### Building a Stack

```
BUILD {
  PUSH "first"
  PUSH "second"
  PUSH "third"
}
```

### Conditional Execution

```
CHECK {
  GATE depth > 2
  PUSH "only if depth > 2"
}
```

### Controlled Iteration

```
ITERATE {
  SATURATE {
    PUSH "item"
    GATE depth < 10
  }
}
```

### Fixed Point Loop

```
CONVERGE {
  SATURATE {
    GATE unbound done
    BIND "done" "yes"
  }
}
```

### State Recording

```
TRACK {
  PUSH "checkpoint1"
  WITNESS
  PUSH "checkpoint2"
  WITNESS
}
```

## Running Tests

```bash
python3 tests/test_vm.py
```

Expected output:
```
Running tests...

✓ test_parse_simple
✓ test_parse_multiple_phases
...
✓ test_witness_trace

============================================================
Results: 14 passed, 0 failed
============================================================
```

## Troubleshooting

### "Parse error: Expected KEYWORD"
- Check that phase names are UPPERCASE
- Verify all braces are properly matched
- Ensure operators are spelled correctly

### "ERR_STACK_OVERFLOW"
- Reduce iterations in SATURATE loops
- Add GATE conditions to limit growth
- Increase --max-stack limit

### "TERM_CYCLE_LIMIT"
- Add GATE conditions to break SATURATE
- Verify fixed point is reachable
- Increase --max-saturate limit

## Next Steps

1. Read `/dsl/operators.md` for detailed operator reference
2. Explore `/vm/execution_phases.md` to understand VM internals
3. Review `/vm/fail_safes.md` for resource limit details
4. Experiment with combining operators in new ways

## Getting Help

- Check documentation in `/dsl` and `/vm` directories
- Run with `--trace` to see execution flow
- Use `check` command to validate syntax before running
- Review example programs for patterns

## Philosophy

Remember: liminal-vm is a symbolic state machine. The semantics of your programs are entirely up to you. The VM guarantees:
- Deterministic execution
- Bounded resources
- Explicit state transitions

What those states *mean* is your domain.
