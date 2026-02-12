"""
Error types for liminal-vm
"""

class LiminalError(Exception):
    """Base exception for all liminal-vm errors"""
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self._format_message())
    
    def _format_message(self):
        if self.line is not None:
            return f"Line {self.line}: {self.message}"
        return self.message

class ParseError(LiminalError):
    """Syntax or semantic error during parsing"""
    pass

class RuntimeError(LiminalError):
    """Error during program execution"""
    pass

class StackOverflowError(RuntimeError):
    """Stack depth exceeded maximum"""
    pass

class BindingsOverflowError(RuntimeError):
    """Bindings count exceeded maximum"""
    pass

class CycleLimitError(RuntimeError):
    """SATURATE iteration limit exceeded"""
    pass

class OperationLimitError(RuntimeError):
    """Total operation budget exceeded"""
    pass

class ArityError(RuntimeError):
    """Operator called with wrong number of arguments"""
    pass

class ConditionError(RuntimeError):
    """Invalid GATE condition"""
    pass

class BreakBlock(Exception):
    """Internal exception to break from SATURATE block"""
    pass

class HaltProgram(Exception):
    """Internal exception to halt program execution"""
    pass
