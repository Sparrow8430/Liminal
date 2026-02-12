# Grammar Specification

## Formal Grammar (EBNF)

```ebnf
program     := phase+
phase       := IDENT "{" operation+ "}"
operation   := operator argument*
operator    := SYMBOL | KEYWORD
argument    := LITERAL | REFERENCE | BLOCK
LITERAL     := STRING | NUMBER
STRING      := '"' [^"]* '"'
NUMBER      := [0-9]+
IDENT       := [A-Z][A-Z0-9_]*
REFERENCE   := [a-z][a-z0-9_]*
BLOCK       := "{" operation+ "}"
SYMBOL      := "PUSH" | "INVERT" | "BIND" | "RELEASE" 
             | "GATE" | "SATURATE" | "WITNESS" | "HALT"
```

## Lexical Rules

### Tokens

**Identifiers (Phase Names)**
- Must start with uppercase letter
- Can contain uppercase letters, digits, underscores
- Examples: `BEGIN`, `TRANSFORM`, `PHASE_1`

**References (Variable Names)**
- Must start with lowercase letter
- Can contain lowercase letters, digits, underscores
- Examples: `above`, `temp_var`, `counter1`

**String Literals**
- Enclosed in double quotes
- No escape sequences in base implementation
- Examples: `"symbol"`, `"state_a"`

**Numeric Literals**
- Integer only
- Unsigned in base implementation
- Examples: `0`, `42`, `1000`

### Whitespace

- Spaces, tabs, newlines are ignored between tokens
- Used only as token separators

### Comments

```
# Single-line comment (optional extension)
```

## Syntax Structure

### Program Structure

A program consists of one or more phases executed sequentially:

```
PHASE_ONE {
  PUSH "initial"
}

PHASE_TWO {
  INVERT
}
```

### Phase Structure

Each phase has:
- A unique identifier (phase name)
- A block of operations enclosed in `{}`
- At least one operation

```
PHASE_NAME {
  OPERATION1 arg1
  OPERATION2
  OPERATION3 arg1 arg2
}
```

### Operation Structure

Operations consist of:
- An operator keyword
- Zero or more arguments (depending on operator arity)

```
PUSH "value"          # Arity 1
INVERT                # Arity 0
BIND "key" "value"    # Arity 2
SATURATE {            # Arity 1 (block)
  PUSH "layer"
}
```

## Parsing Rules

### Phase Execution Order

Phases execute in the order they appear in the source file.

### Operation Execution Order

Within a phase, operations execute sequentially from top to bottom.

### Block Scope

Blocks (used with `SATURATE`, `GATE`) create nested execution contexts but do not create new variable scopes.

## Validation Rules

A syntactically valid program must:

1. **Have at least one phase**
2. **Each phase must have at least one operation**
3. **All operations must use defined operators**
4. **Operator arity must match arguments provided**
5. **String literals must be properly quoted**
6. **Phase names must be unique** (optional: can warn on duplicates)

## Error Cases

### Syntax Errors

```
# Missing closing brace
PHASE {
  PUSH "test"

# Invalid operator
PHASE {
  UNDEFINED_OP
}

# Mismatched quotes
PHASE {
  PUSH "unclosed
}

# Wrong arity
PHASE {
  PUSH          # PUSH requires 1 argument
}
```

### Semantic Errors (Caught at Parse Time)

```
# Duplicate phase names (warning)
BEGIN { PUSH "a" }
BEGIN { PUSH "b" }
```

## Extension Points

The grammar is designed to allow future extensions:

- Additional operator keywords
- Type annotations
- Inline phase parameters
- Macro definitions

But base implementation focuses on minimal, unambiguous syntax.

## Example: Annotated Parse

```
BEGIN {           # Phase declaration, name="BEGIN"
  PUSH "start"    # Operation: PUSH, arg="start"
  WITNESS         # Operation: WITNESS, no args
}                 # End phase block

LOOP {            # Phase declaration, name="LOOP"
  SATURATE {      # Operation: SATURATE, arg=<block>
    PUSH "x"      #   Block operation
    GATE depth    #   Block operation with reference
  }               # End saturate block
}                 # End phase block
```

## Reserved Keywords

The following are reserved and cannot be used as identifiers:

- `PUSH`
- `INVERT`
- `BIND`
- `RELEASE`
- `GATE`
- `SATURATE`
- `WITNESS`
- `HALT`

## Case Sensitivity

The language is **case-sensitive**:
- `BEGIN` ≠ `begin`
- Phase names must be uppercase
- Operators must be uppercase
- References must be lowercase
