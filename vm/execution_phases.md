# Execution Phases

## Overview

The liminal-vm executes programs in four distinct phases, ensuring clean separation of concerns and predictable behavior.

```
┌─────────┐
│  PARSE  │ ─── Syntax validation
└────┬────┘
     │
┌────▼────────┐
│ INITIALIZE  │ ─── State setup
└────┬────────┘
     │
┌────▼────┐
│ EXECUTE │ ─── Operation processing
└────┬────┘
     │
┌────▼─────┐
│ FINALIZE │ ─── Output generation
└──────────┘
```

---

## Phase 1: PARSE

**Purpose:** Transform source code into executable representation

### Steps

1. **Tokenization**
   - Read source file
   - Split into tokens (keywords, identifiers, literals, braces)
   - Strip whitespace and comments

2. **Lexical Analysis**
   - Validate token types
   - Check reserved keywords
   - Verify identifier naming conventions

3. **Syntax Analysis**
   - Build Abstract Syntax Tree (AST)
   - Verify grammar rules
   - Check brace matching
   - Validate phase structure

4. **Semantic Validation**
   - Check operator arity
   - Verify argument types
   - Detect undefined operators
   - Validate GATE conditions
   - Check for empty phases

### AST Structure

```python
Program
  └── Phase[]
        ├── name: str
        └── operations: Operation[]
              ├── operator: str
              └── arguments: Argument[]
                    ├── type: LITERAL | REFERENCE | BLOCK
                    └── value: str | Block
```

### Parse Outputs

**Success:**
- AST ready for execution
- Proceed to INITIALIZE

**Failure:**
- Error type (syntax/semantic)
- Line and column number
- Error message
- Exit with `ERR_PARSE`

### Example

**Input:**
```
BEGIN {
  PUSH "start"
  WITNESS
}
```

**AST:**
```json
{
  "phases": [
    {
      "name": "BEGIN",
      "operations": [
        {
          "operator": "PUSH",
          "arguments": [
            {"type": "LITERAL", "value": "start"}
          ]
        },
        {
          "operator": "WITNESS",
          "arguments": []
        }
      ]
    }
  ]
}
```

---

## Phase 2: INITIALIZE

**Purpose:** Set up VM state for execution

### Steps

1. **Allocate Stack**
   ```python
   stack = []
   stack_max = 256  # From config
   ```

2. **Allocate Bindings Map**
   ```python
   bindings = {}
   bindings_max = 1024  # From config
   ```

3. **Initialize Counters**
   ```python
   phase_counter = 0
   operation_counter = 0
   max_operations = 100000  # From config
   ```

4. **Initialize Trace**
   ```python
   trace = []
   trace_enabled = True/False  # From flags
   ```

5. **Set Execution State**
   ```python
   halted = False
   error = None
   ```

### Configuration

Initialize uses values from:
- Command-line arguments
- Configuration file
- Built-in defaults

### State Snapshot (Post-Initialization)

```python
{
  "stack": [],
  "bindings": {},
  "phase_counter": 0,
  "operation_counter": 0,
  "halted": False,
  "trace": []
}
```

---

## Phase 3: EXECUTE

**Purpose:** Run the program operations

### Main Loop

```python
for phase in program.phases:
    if halted:
        break
    
    phase_counter += 1
    
    for operation in phase.operations:
        if halted:
            break
        
        # Check resource limits
        if operation_counter >= max_operations:
            exit_with(TERM_OP_LIMIT)
        
        if len(stack) > stack_max:
            exit_with(ERR_STACK_OVERFLOW)
        
        # Execute operation
        execute_operation(operation)
        operation_counter += 1
```

### Operation Dispatch

```python
def execute_operation(op):
    match op.operator:
        case "PUSH":
            stack.append(op.arguments[0].value)
        
        case "INVERT":
            stack.reverse()
        
        case "BIND":
            key = op.arguments[0].value
            value = op.arguments[1].value
            bindings[key] = value
        
        case "RELEASE":
            key = op.arguments[0].value
            bindings.pop(key, None)
        
        case "GATE":
            if not evaluate_condition(op.arguments[0]):
                raise BreakBlock()
        
        case "SATURATE":
            execute_saturate(op.arguments[0].block)
        
        case "WITNESS":
            record_checkpoint()
        
        case "HALT":
            halted = True
```

### SATURATE Execution

```python
def execute_saturate(block):
    iteration = 0
    max_iterations = 1000
    
    while iteration < max_iterations:
        # Capture state before
        state_before = snapshot_state()
        
        # Execute block
        try:
            execute_block(block)
        except BreakBlock:
            break
        
        # Capture state after
        state_after = snapshot_state()
        
        # Check fixed point
        if state_before == state_after:
            break
        
        iteration += 1
    
    if iteration >= max_iterations:
        exit_with(TERM_CYCLE_LIMIT)
```

### State Snapshot

```python
def snapshot_state():
    return {
        "stack": stack.copy(),
        "bindings": bindings.copy()
    }
```

### Trace Recording

```python
def record_checkpoint():
    if trace_enabled:
        trace.append({
            "phase": current_phase_name,
            "operation": operation_counter,
            "stack": stack.copy(),
            "bindings": bindings.copy()
        })
```

### Error Handling

```python
try:
    execute_operation(op)
except StackOverflow:
    exit_with(ERR_STACK_OVERFLOW)
except InvalidOperation:
    exit_with(ERR_INVALID_OP)
except TypeError:
    exit_with(ERR_TYPE)
```

---

## Phase 4: FINALIZE

**Purpose:** Generate output and clean up

### Steps

1. **Determine Exit Status**
   ```python
   if error:
       status = error.code
   elif halted:
       status = "HALTED"
   else:
       status = "COMPLETE"
   ```

2. **Serialize Final State**
   ```python
   final_state = {
       "stack": stack,
       "bindings": bindings,
       "depth": len(stack),
       "binding_count": len(bindings)
   }
   ```

3. **Generate Execution Summary**
   ```python
   summary = {
       "status": status,
       "phases_executed": phase_counter,
       "operations_executed": operation_counter,
       "final_state": final_state
   }
   ```

4. **Build Trace Output** (if enabled)
   ```python
   trace_output = {
       "checkpoints": trace,
       "total_checkpoints": len(trace)
   }
   ```

5. **Format Output**
   - JSON (default)
   - Human-readable text
   - Compact format

### Output Examples

**Success:**
```json
{
  "status": "COMPLETE",
  "phases_executed": 3,
  "operations_executed": 47,
  "final_state": {
    "stack": ["result"],
    "bindings": {"key": "value"},
    "depth": 1,
    "binding_count": 1
  }
}
```

**Error:**
```json
{
  "status": "TERM_CYCLE_LIMIT",
  "error_message": "SATURATE exceeded 1000 iterations",
  "phase": "EXPAND",
  "operation": 1042,
  "final_state": {
    "stack": ["x", "x", "x", "..."],
    "depth": 1000
  }
}
```

**With Trace:**
```json
{
  "status": "COMPLETE",
  "summary": {...},
  "trace": [
    {
      "phase": "BEGIN",
      "operation": 2,
      "stack": ["initial"],
      "bindings": {}
    },
    {
      "phase": "TRANSFORM",
      "operation": 5,
      "stack": ["transformed"],
      "bindings": {"result": "true"}
    }
  ]
}
```

---

## Phase Interactions

### Data Flow

```
PARSE
  └─> AST
       └─> INITIALIZE
            └─> Initial State
                 └─> EXECUTE
                      └─> Final State
                           └─> FINALIZE
                                └─> Output
```

### State Transitions

```
NULL
  ↓ (PARSE)
PARSED
  ↓ (INITIALIZE)
READY
  ↓ (EXECUTE)
RUNNING
  ↓ (operation by operation)
RUNNING
  ↓ (completion/error)
TERMINATED
  ↓ (FINALIZE)
FINALIZED
```

### Error Recovery

Each phase handles errors independently:

- **PARSE:** Cannot recover, exits immediately
- **INITIALIZE:** Cannot recover, exits immediately  
- **EXECUTE:** Captures error, proceeds to FINALIZE
- **FINALIZE:** Always completes (best-effort output)

---

## Implementation Considerations

### Separation of Concerns

Each phase has a single responsibility:
- PARSE: Syntax → AST
- INITIALIZE: AST → State
- EXECUTE: State → State′
- FINALIZE: State → Output

No phase depends on implementation details of others.

### Testability

Each phase can be tested independently:

```python
# Test PARSE
ast = parse(source_code)
assert ast.phases[0].name == "BEGIN"

# Test EXECUTE (mock initialize)
vm = VM(mock_state)
vm.execute(ast)
assert vm.stack == expected_stack
```

### Performance

Phase breakdown enables optimization:

- **PARSE:** Cache AST for repeated runs
- **INITIALIZE:** Pre-allocate based on AST analysis
- **EXECUTE:** JIT compilation of hot paths (future)
- **FINALIZE:** Lazy trace serialization

### Debugging

Phase boundaries provide natural debug points:

```bash
# Stop after parse
liminal-vm parse program.lmn --dump-ast

# Stop after execute
liminal-vm run program.lmn --no-finalize

# Trace each phase
liminal-vm run program.lmn --debug-phases
```

---

## Future Extensions

Potential additional phases:

- **OPTIMIZE:** AST optimization (dead code elimination)
- **VALIDATE:** Deeper semantic analysis (reachability)
- **INSTRUMENT:** Insert profiling code
- **COMPILE:** Generate bytecode from AST

Current four-phase design is minimal but extensible.
