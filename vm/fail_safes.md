# Fail-Safes

## Overview

The liminal-vm implements multiple layers of protection to ensure bounded execution and prevent resource exhaustion, infinite loops, and undefined behavior.

---

## Resource Guards

### Operation Budget

**Protection Against:** Runaway execution from excessive operations

**Mechanism:**
- Global counter incremented on each operation
- Checked before every operation execution
- Terminates when budget exceeded

**Default Limit:** 100,000 operations

**Configuration:**
```bash
--max-ops 50000
```

**Error Code:** `TERM_OP_LIMIT`

**Example Trigger:**
```
LOOP {
  SATURATE {
    PUSH "infinite"
    PUSH "more"
    PUSH "endless"
    # No GATE - runs until op limit
  }
}
```

---

### Stack Depth Limit

**Protection Against:** Stack overflow from unbounded growth

**Mechanism:**
- Stack size checked before each PUSH
- Terminates if size would exceed limit
- Prevents memory exhaustion

**Default Limit:** 256 symbols

**Configuration:**
```bash
--max-stack 128
```

**Error Code:** `ERR_STACK_OVERFLOW`

**Example Trigger:**
```
OVERFLOW {
  SATURATE {
    PUSH "x"
    GATE depth < 1000  # Attempts 1000 depth
  }
}
# Fails at depth 256
```

**Stack Depth Calculation:**
```python
depth = len(stack)
if depth >= max_stack:
    raise StackOverflowError()
```

---

### Bindings Limit

**Protection Against:** Memory exhaustion from excessive key-value pairs

**Mechanism:**
- Binding count checked before each BIND
- Terminates if count would exceed limit

**Default Limit:** 1,024 bindings

**Configuration:**
```bash
--max-bindings 512
```

**Error Code:** `ERR_BINDINGS_OVERFLOW`

**Example Trigger:**
```
CREATE {
  SATURATE {
    BIND counter "value"
    # Uses same key - no overflow
  }
}

CREATE_MANY {
  SATURATE {
    BIND unique_key counter
    # Different key each iteration - hits limit
  }
}
```

---

## Loop Protection

### SATURATE Iteration Limit

**Protection Against:** Infinite loops in SATURATE blocks

**Mechanism:**
- Per-SATURATE iteration counter
- Independent counter for each SATURATE instance
- Terminates single loop when exceeded

**Default Limit:** 1,000 iterations

**Configuration:**
```bash
--max-saturate 500
```

**Error Code:** `TERM_CYCLE_LIMIT`

**Example Trigger:**
```
EXPAND {
  SATURATE {
    PUSH "layer"
    # Missing GATE condition - runs 1000 times then stops
  }
}
```

**Counter Reset:**
```python
def execute_saturate(block):
    iteration = 0  # Fresh counter for this SATURATE
    while iteration < max_saturate_iterations:
        execute_block(block)
        iteration += 1
```

---

### Fixed Point Detection

**Protection Against:** Unnecessary iterations when state stabilizes

**Mechanism:**
- Snapshot state before and after each SATURATE iteration
- Deep equality comparison
- Early termination on match

**No Configuration:** Always enabled

**Benefit:** Reduces operation count, faster termination

**Example:**
```
CONVERGE {
  SATURATE {
    GATE bound "done"
    BIND "done" "yes"
  }
}
# First iteration: binds "done"
# Second iteration: GATE fails immediately
# Fixed point detected - stops after 2 iterations
```

**State Comparison:**
```python
def fixed_point_reached(before, after):
    return (
        before["stack"] == after["stack"] and
        before["bindings"] == after["bindings"]
    )
```

---

## Type Safety

### Operator Arity Checking

**Protection Against:** Malformed operations from wrong argument count

**Mechanism:**
- Parse-time validation of argument count
- Runtime verification before execution

**Error Code:** `ERR_ARITY`

**Example Trigger:**
```
BROKEN {
  PUSH          # Missing argument
  BIND "key"    # Missing second argument
}
```

**Validation:**
```python
ARITY = {
    "PUSH": 1,
    "INVERT": 0,
    "BIND": 2,
    "RELEASE": 1,
    # ...
}

if len(operation.arguments) != ARITY[operation.operator]:
    raise ArityError()
```

---

### Condition Validation

**Protection Against:** Invalid GATE conditions

**Mechanism:**
- Parse-time syntax check
- Runtime evaluation safety

**Error Code:** `ERR_CONDITION`

**Valid Conditions:**
```
depth < N
depth > N
depth == N
bound <key>
unbound <key>
```

**Example Trigger:**
```
INVALID {
  GATE invalid_syntax    # Parse error
  GATE depth = 5         # Wrong operator (= not ==)
}
```

---

## Input Validation

### Source Code Limits

**Protection Against:** Maliciously large source files

**Mechanism:**
- File size check before parsing
- Maximum source length enforced

**Default Limit:** 1 MB source file

**Configuration:**
```bash
--max-source-size 512K
```

**Error Code:** `ERR_SOURCE_TOO_LARGE`

---

### Token Limits

**Protection Against:** Parser DoS from excessive tokens

**Mechanism:**
- Token count tracked during lexical analysis
- Terminates parsing if exceeded

**Default Limit:** 100,000 tokens

**Error Code:** `ERR_TOO_MANY_TOKENS`

---

### Nesting Depth Limit

**Protection Against:** Stack overflow from deeply nested blocks

**Mechanism:**
- Track block nesting depth during parsing
- Reject programs exceeding limit

**Default Limit:** 32 levels

**Configuration:**
```bash
--max-nesting 16
```

**Error Code:** `ERR_NESTING_TOO_DEEP`

**Example Trigger:**
```
BEGIN {
  SATURATE {
    SATURATE {
      SATURATE {
        # ... 30 more levels ...
      }
    }
  }
}
```

---

## Execution Safeguards

### Phase Timeout

**Protection Against:** Single phase taking excessive time

**Mechanism:**
- Wall-clock timer for each phase
- Terminates if phase exceeds time limit

**Default Limit:** 30 seconds per phase

**Configuration:**
```bash
--phase-timeout 10
```

**Error Code:** `TERM_TIMEOUT`

**Note:** Disabled by default, opt-in feature

---

### Memory Monitoring

**Protection Against:** Excessive memory consumption

**Mechanism:**
- Periodic memory usage checks
- Terminates if VM memory exceeds limit

**Default Limit:** 100 MB

**Configuration:**
```bash
--max-memory 50M
```

**Error Code:** `TERM_MEMORY_LIMIT`

**Checking:**
```python
import psutil

if psutil.Process().memory_info().rss > max_memory:
    raise MemoryLimitError()
```

---

## Error Handling

### Graceful Degradation

All fail-safes follow a consistent error handling pattern:

1. **Detect** violation
2. **Capture** current state
3. **Log** diagnostic information
4. **Terminate** execution cleanly
5. **Report** via standard error format

### Error Context

Every error includes:
```json
{
  "error_code": "TERM_CYCLE_LIMIT",
  "error_message": "SATURATE exceeded 1000 iterations",
  "phase": "EXPAND",
  "operation_number": 1247,
  "line_number": 12,
  "stack_depth": 1000,
  "binding_count": 5
}
```

### No Silent Failures

The VM never:
- Silently truncates data
- Continues execution after limit
- Produces partial output without warning
- Hides resource consumption

All violations are explicit and reported.

---

## Limit Interactions

### Cascading Limits

Multiple limits may interact:

```
COMPLEX {
  SATURATE {              # Saturate limit: 1000
    PUSH "x"              # Stack limit: 256
    PUSH "y"              # Op limit: 100000
  }
}
```

**Termination:** Whichever limit is hit first

**Example:**
- Iteration 256: Stack limit hit
- Never reaches saturate limit (1000)
- Never reaches op limit (100000)

### Limit Priority

When multiple limits apply:

1. **Parse errors** - Stop before execution
2. **Stack overflow** - Stop immediately
3. **Bindings overflow** - Stop immediately
4. **Cycle limit** - Stop current SATURATE
5. **Op limit** - Stop entire program
6. **Timeout** - Stop current phase

---

## Configuration Recommendations

### Conservative (High Security)

```bash
--max-ops 10000 \
--max-stack 64 \
--max-saturate 100 \
--max-bindings 128 \
--phase-timeout 5
```

**Use Case:** Untrusted code, sandboxed execution

---

### Standard (Default)

```bash
--max-ops 100000 \
--max-stack 256 \
--max-saturate 1000 \
--max-bindings 1024
```

**Use Case:** General purpose, trusted code

---

### Permissive (Development)

```bash
--max-ops 1000000 \
--max-stack 4096 \
--max-saturate 10000 \
--max-bindings 8192
```

**Use Case:** Testing, exploration, long-running programs

---

## Bypass Mechanisms

**There are no bypass mechanisms.**

Limits cannot be disabled or set to infinity. This is by design.

Minimum values:
- `--max-ops 1`
- `--max-stack 1`
- `--max-saturate 1`
- `--max-bindings 1`

Maximum values (enforced):
- `--max-ops 1000000`
- `--max-stack 4096`
- `--max-saturate 10000`
- `--max-bindings 8192`

---

## Testing Fail-Safes

### Validation Tests

Each fail-safe should be tested with:

1. **Trigger program** - Deliberately violates limit
2. **Near-limit program** - Just below threshold
3. **Recovery test** - Confirm graceful termination
4. **Error message test** - Verify diagnostic quality

### Example Test

```python
def test_stack_overflow():
    program = """
    TEST {
        SATURATE {
            PUSH "x"
            GATE depth < 1000
        }
    }
    """
    
    result = vm.run(program, max_stack=256)
    
    assert result.status == "ERR_STACK_OVERFLOW"
    assert result.stack_depth == 256
    assert "stack" in result.error_message.lower()
```

---

## Implementation Checklist

For each fail-safe:

- [ ] Documented in this file
- [ ] Configurable via CLI
- [ ] Default value chosen
- [ ] Min/max bounds enforced
- [ ] Error code defined
- [ ] Error message clear
- [ ] Test coverage >90%
- [ ] Performance impact measured
- [ ] User documentation updated

---

## Performance Impact

Fail-safe overhead (per operation):

| Guard | Cost | Frequency |
|-------|------|-----------|
| Op counter | O(1) increment | Every op |
| Stack depth check | O(1) comparison | Every PUSH |
| Bindings check | O(1) comparison | Every BIND |
| Fixed point | O(n) comparison | Each SATURATE iteration |
| Memory check | O(1) syscall | Every 1000 ops |

**Total overhead:** ~3-5% of execution time

**Trade-off:** Worthwhile for guaranteed termination
