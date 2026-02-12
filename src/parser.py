"""
Parser for liminal-vm programs
"""

import re
from dataclasses import dataclass, field
from typing import List, Any, Optional
from errors import ParseError

@dataclass
class Argument:
    type: str  # LITERAL, REFERENCE, BLOCK
    value: Any
    
    def to_dict(self):
        if self.type == 'BLOCK':
            return {
                'type': self.type,
                'operations': [op.to_dict() for op in self.value]
            }
        return {'type': self.type, 'value': self.value}

@dataclass
class Operation:
    operator: str
    arguments: List[Argument] = field(default_factory=list)
    line: int = 0
    
    def to_dict(self):
        return {
            'operator': self.operator,
            'arguments': [arg.to_dict() for arg in self.arguments]
        }

@dataclass
class Phase:
    name: str
    operations: List[Operation] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'name': self.name,
            'operations': [op.to_dict() for op in self.operations]
        }

@dataclass
class Program:
    phases: List[Phase] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'phases': [phase.to_dict() for phase in self.phases]
        }

# Operator arity definitions
OPERATOR_ARITY = {
    'PUSH': 1,
    'INVERT': 0,
    'BIND': 2,
    'RELEASE': 1,
    'GATE': 1,
    'SATURATE': 1,
    'WITNESS': 0,
    'HALT': 0
}

class Tokenizer:
    """Lexical analyzer for liminal-vm"""
    
    TOKEN_PATTERNS = [
        ('COMMENT', r'#[^\n]*'),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('STRING', r'"[^"]*"'),
        ('NUMBER', r'\d+'),
        ('KEYWORD', r'[A-Z_][A-Z0-9_]*'),
        ('IDENT', r'[a-z_][a-z0-9_]*'),
        ('SYMBOL', r'[<>=!]+'),
        ('WHITESPACE', r'[ \t\n\r]+'),
    ]
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
    
    def tokenize(self) -> List[tuple]:
        """Convert source into tokens"""
        pattern = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.TOKEN_PATTERNS)
        regex = re.compile(pattern)
        
        for match in regex.finditer(self.source):
            token_type = match.lastgroup
            token_value = match.group()
            
            if token_type == 'WHITESPACE':
                # Track line numbers
                self.line += token_value.count('\n')
                if '\n' in token_value:
                    self.column = len(token_value.split('\n')[-1]) + 1
                else:
                    self.column += len(token_value)
                continue
            
            if token_type == 'COMMENT':
                self.line += 1
                self.column = 1
                continue
            
            if token_type == 'STRING':
                # Remove quotes
                token_value = token_value[1:-1]
            
            self.tokens.append((token_type, token_value, self.line, self.column))
            self.column += len(match.group())
        
        return self.tokens

class Parser:
    """Syntax analyzer for liminal-vm"""
    
    def __init__(self, tokens: List[tuple], filename: str):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0
    
    def current_token(self) -> Optional[tuple]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self, expected_type: str = None) -> tuple:
        token = self.current_token()
        if token is None:
            raise ParseError("Unexpected end of file")
        
        token_type, value, line, column = token
        
        if expected_type and token_type != expected_type:
            raise ParseError(
                f"Expected {expected_type}, got {token_type} '{value}'",
                line=line
            )
        
        self.pos += 1
        return token
    
    def peek(self) -> Optional[str]:
        token = self.current_token()
        return token[0] if token else None
    
    def parse_program(self) -> Program:
        """Parse entire program"""
        program = Program()
        
        while self.current_token():
            phase = self.parse_phase()
            program.phases.append(phase)
        
        if not program.phases:
            raise ParseError("Program must have at least one phase")
        
        return program
    
    def parse_phase(self) -> Phase:
        """Parse a phase block"""
        token_type, name, line, _ = self.consume('KEYWORD')
        phase = Phase(name=name)
        
        self.consume('LBRACE')
        
        # Parse operations until closing brace
        while self.peek() != 'RBRACE':
            if self.current_token() is None:
                raise ParseError(f"Unclosed phase '{name}'", line=line)
            
            operation = self.parse_operation()
            phase.operations.append(operation)
        
        self.consume('RBRACE')
        
        if not phase.operations:
            raise ParseError(f"Phase '{name}' must have at least one operation", line=line)
        
        return phase
    
    def parse_operation(self) -> Operation:
        """Parse a single operation"""
        token_type, operator, line, _ = self.consume('KEYWORD')
        
        if operator not in OPERATOR_ARITY:
            raise ParseError(f"Unknown operator '{operator}'", line=line)
        
        operation = Operation(operator=operator, line=line)
        expected_arity = OPERATOR_ARITY[operator]
        
        # Special case: SATURATE takes a block
        if operator == 'SATURATE':
            self.consume('LBRACE')
            block_ops = []
            while self.peek() != 'RBRACE':
                if self.current_token() is None:
                    raise ParseError("Unclosed SATURATE block", line=line)
                block_ops.append(self.parse_operation())
            self.consume('RBRACE')
            
            operation.arguments.append(Argument(type='BLOCK', value=block_ops))
            return operation
        
        # Parse regular arguments
        for _ in range(expected_arity):
            arg = self.parse_argument()
            operation.arguments.append(arg)
        
        return operation
    
    def parse_argument(self) -> Argument:
        """Parse an operation argument"""
        token = self.current_token()
        
        if token is None:
            raise ParseError("Expected argument")
        
        token_type, value, line, _ = token
        
        if token_type == 'STRING':
            self.consume()
            return Argument(type='LITERAL', value=value)
        
        if token_type == 'NUMBER':
            self.consume()
            return Argument(type='LITERAL', value=int(value))
        
        if token_type == 'IDENT':
            self.consume()
            return Argument(type='REFERENCE', value=value)
        
        if token_type == 'SYMBOL':
            # For GATE conditions - consume the whole condition
            self.consume()
            condition = value
            
            # Check for comparison operators with value
            if self.peek() in ('NUMBER', 'IDENT'):
                _, operand, _, _ = self.consume()
                condition += ' ' + operand
            
            return Argument(type='REFERENCE', value=condition)
        
        raise ParseError(f"Unexpected token type {token_type} as argument", line=line)

def parse_program(source: str, filename: str = "<input>") -> Program:
    """Main entry point for parsing"""
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    
    parser = Parser(tokens, filename)
    program = parser.parse_program()
    
    return program
