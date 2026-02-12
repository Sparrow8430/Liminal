# Termination Conditions

## Overview

The liminal-vm guarantees termination of all programs through bounded resource consumption and explicit halting conditions.

## Termination Criteria

A program terminates when **any** of the following conditions are met:

### 1. Normal Completion

All phases have executed successfully and the program reaches its natural end.

**Status Code:** `COMPLETE`

**Example:**
```
BEGIN {
  PUSH "done"
}
# Exits normally after BEGIN completes
```

---

### 2. Explicit Halt

The `HALT` operator is encountered during execution.

**Status Code:** `HALTED`

**Example:**
```
BEGIN {
  PUSH "early"
  HALT
}

UNREACHABLE {
  PUSH "never"
}
# Exits at HALT, UNREACHABLE never runs
```

---

### 3. Operation Budget Exceeded

The total number of operations executed exceeds the maximum allowed.

**Default Limit:** 100,000 operations

**Status Code:** `TERM_OP_LIMIT`

**What Counts as an Operation:**
- Each operator execution (PUSH, INVERT, BIND, etc.)
- Each iteration of SATURATE block counts separately
- Phase transitions do NOT count

**Example:**
```
LOOP {
  SATURATE {
    PUSH "infinite"
    # No GATE to break - will hit iteration limit first
  }
}
# Terminates at 1000 SATURATE iterations
```

**Rationale:** Prevents runaway execution from malformed or malicious programs.

---

### 4. Cycle Limit (SATURATE)

A single `SATURATE` block exceeds its maximum iteration count.

**Default Limit:** 1,000 iterations per SATURATE

**Status Code:** `TERM_CYCLE_LIMIT`

**Example:**
```
EXPAND {
  SATURATE {
    PUSH "layer"
    # Missing GATE - runs until iteration limit
  }
}
# Terminates after 1000 iterations
```

**Iteration Counting:**
- Resets for each new SATURATE block
- Nested SATURATE blocks each have their own counter

**Rationale:** Prevents infinite loops even when total op budget is not reached.

---

### 5. Stack Overflow

Stack depth exceeds maximum allowed size.

**Default Limit:** 256 symbols

**Status Code:** `ERR_STACK_OVERFLOW`

**Example:**
```
OVERFLOW {
  SATURATE {
    PUSH "x"
    GATE depth < 1000  # Tries to exceed stack limit
  }
}
# Terminates when stack reaches 256
```

**Rationale:** Prevents memory exhaustion.

---

### 6. Parse Error

Program fails syntactic or semantic validation before execution begins.

**Status Code:** `ERR_PARSE`

**Common Causes:**
- Malformed syntax
- Undefined operator
- Arity mismatch
- Unterminated string literal
- Missing braces

**Example:**
```
BROKEN {
  PUSH          # Missing argument
}
# Never executes - parse error
```

---

### 7. Runtime Error

An operator encounters an invalid condition during execution.

**Status Codes:**
- `ERR_INVALID_OP` - Undefined operator encountered
- `ERR_TYPE` - Type mismatch
- `ERR_ARITY` - Wrong number of arguments
- `ERR_CONDITION` - Invalid GATE condition

**Example:**
```
BEGIN {
  BIND "key"    # Missing second argument
}
# Runtime error: BIND requires 2 arguments
```

---

## Resource Limits

### Configurable Limits

All limits can be configured at VM startup:

| Resource | Default | Min | Max |
|----------|---------|-----|-----|
| Max Operations | 100,000 | 1 | 1,000,000 |
| Max Stack Depth | 256 | 1 | 4,096 |
| Max SATURATE Iterations | 1,000 | 1 | 10,000 |
| Max Bindings | 1,024 | 1 | 8,192 |

### Command-Line Override

```bash
python3 src/liminal.py run program.lmn \
  --max-ops 50000 \
  --max-stack 128 \
  --max-saturate 500 \
  --max-bindings 512
```

---

## Fixed Point Detection

### SATURATE Termination

`SATURATE` blocks can terminate early through fixed point detection:

**Fixed Point:** State where another iteration would produce no changes.

**Detection:**
```
Before iteration: Stack=[a,b], Bindings={x:y}
After iteration:  Stack=[a,b], Bindings={x:y}
Result: Fixed point - SATURATE terminates
```

**Example:**
```
SATURATE {
  GATE bound "ready"
  PUSH "init"
  BIND "ready" "true"
}
# First iteration: Adds "init", binds "ready"
# Second iteration: GATE fails (ready is bound), exits
# Terminates after 2 iterations
```

**Comparison:**
- Deep equality check on stack (order matters)
- Deep equality check on bindings

---

## Termination Guarantees

### Every Program Terminates

**Proof Sketch:**

1. **Finite operations:** Op budget is bounded
2. **Finite iterations:** SATURATE is bounded per-loop
3. **Finite nesting:** Call stack depth is implicit in program structure
4. **No recursion:** Phases cannot call other phases
5. **No dynamic code:** No eval or code generation

Therefore: All programs terminate in finite time.

### Termination Time Bounds

**Worst Case:** O(max_ops)

**Typical Case:** O(phases × ops_per_phase)

**Best Case:** O(1) if HALT in first phase

---

## Diagnostic Information

On termination, the VM provides:

### Exit Status
- Status code (COMPLETE, HALTED, ERR_*, TERM_*)
- Exit message

### State Snapshot
- Final stack contents
- Final bindings
- Last executed phase
- Last executed operation

### Execution Trace
- Number of phases executed
- Total operations executed
- Number of WITNESS checkpoints
- Detailed trace (if enabled)

**Example Output:**
```
Status: TERM_CYCLE_LIMIT
Message: SATURATE exceeded 1000 iterations in phase EXPAND
Phase: EXPAND (2 of 3)
Operation: SATURATE
Total Operations: 1247
Stack Depth: 1000
Bindings: 0
```

---

## Non-Termination in Theory

Without resource limits, these programs would not terminate:

```
# Infinite stack growth
INFINITE_STACK {
  SATURATE {
    PUSH "x"
  }
}

# Infinite iterations with no state change
INFINITE_LOOP {
  SATURATE {
    WITNESS
  }
}
```

But in practice, resource limits ensure termination:
- First hits stack overflow at 256 depth
- Second hits iteration limit at 1000

---

## Termination vs. Correctness

**Termination guarantees:**
- Program will stop in finite time

**Termination does NOT guarantee:**
- Program produces meaningful output
- Program achieves intended goal
- Final state is "correct"

The VM ensures bounded execution, but semantic correctness is the programmer's responsibility.

---

## Implementation Notes

### Termination Checking

Checks are performed:
- **Before each operation:** Check op budget, stack depth
- **Each SATURATE iteration:** Check cycle limit, fixed point
- **After each phase:** Check if HALT was encountered

### Performance Impact

Resource checking adds minimal overhead:
- Operation counter: O(1) increment
- Stack depth check: O(1) comparison
- Fixed point check: O(stack_size + binding_count) comparison

Typical overhead: <5% of execution time

### Safety Trade-offs

Stricter limits:
- ✓ Faster termination
- ✓ Lower resource usage
- ✗ Fewer programs complete successfully

Looser limits:
- ✓ More programs complete
- ✓ More expressive
- ✗ Longer worst-case runtime
- ✗ Higher resource usage

Default limits are chosen for reasonable balance.
