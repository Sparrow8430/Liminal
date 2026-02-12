"""
Virtual Machine for liminal-vm
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from copy import deepcopy
from errors import (
    StackOverflowError, BindingsOverflowError, CycleLimitError,
    OperationLimitError, ConditionError, BreakBlock, HaltProgram
)
from parser import Program, Phase, Operation

@dataclass
class VMConfig:
    """VM configuration"""
    max_operations: int = 100000
    max_stack_depth: int = 256
    max_saturate_iterations: int = 1000
    max_bindings: int = 1024
    trace_enabled: bool = False

@dataclass
class ExecutionResult:
    """Result of program execution"""
    status: str
    phases_executed: int
    operations_executed: int
    final_state: Dict[str, Any]
    trace: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self):
        result = {
            'status': self.status,
            'phases_executed': self.phases_executed,
            'operations_executed': self.operations_executed,
            'final_state': self.final_state
        }
        
        if self.error_message:
            result['error_message'] = self.error_message
        
        if self.trace:
            result['trace'] = self.trace
        
        return result

class VirtualMachine:
    """Execution engine for liminal-vm programs"""
    
    def __init__(self, config: VMConfig = None):
        self.config = config or VMConfig()
        self.reset()
    
    def reset(self):
        """Reset VM state"""
        self.stack = []
        self.bindings = {}
        self.phase_counter = 0
        self.operation_counter = 0
        self.halted = False
        self.trace = []
        self.current_phase_name = None
    
    def execute(self, program: Program) -> ExecutionResult:
        """Execute a parsed program"""
        self.reset()
        
        try:
            for phase in program.phases:
                if self.halted:
                    break
                
                self.current_phase_name = phase.name
                self.phase_counter += 1
                self.execute_phase(phase)
            
            status = 'HALTED' if self.halted else 'COMPLETE'
            error_message = None
            
        except HaltProgram:
            status = 'HALTED'
            error_message = None
            
        except StackOverflowError as e:
            status = 'ERR_STACK_OVERFLOW'
            error_message = str(e)
            
        except BindingsOverflowError as e:
            status = 'ERR_BINDINGS_OVERFLOW'
            error_message = str(e)
            
        except CycleLimitError as e:
            status = 'TERM_CYCLE_LIMIT'
            error_message = str(e)
            
        except OperationLimitError as e:
            status = 'TERM_OP_LIMIT'
            error_message = str(e)
            
        except ConditionError as e:
            status = 'ERR_CONDITION'
            error_message = str(e)
        
        return ExecutionResult(
            status=status,
            phases_executed=self.phase_counter,
            operations_executed=self.operation_counter,
            final_state={
                'stack': self.stack.copy(),
                'bindings': self.bindings.copy(),
                'depth': len(self.stack),
                'binding_count': len(self.bindings)
            },
            trace=self.trace.copy() if self.config.trace_enabled else [],
            error_message=error_message
        )
    
    def execute_phase(self, phase: Phase):
        """Execute a single phase"""
        for operation in phase.operations:
            if self.halted:
                break
            self.execute_operation(operation)
    
    def execute_operation(self, operation: Operation):
        """Execute a single operation"""
        # Check operation limit
        if self.operation_counter >= self.config.max_operations:
            raise OperationLimitError(
                f"Operation limit exceeded ({self.config.max_operations})"
            )
        
        self.operation_counter += 1
        
        # Dispatch to operator implementation
        operator = operation.operator
        args = operation.arguments
        
        if operator == 'PUSH':
            self.op_push(args[0].value)
        
        elif operator == 'INVERT':
            self.op_invert()
        
        elif operator == 'BIND':
            self.op_bind(args[0].value, args[1].value)
        
        elif operator == 'RELEASE':
            self.op_release(args[0].value)
        
        elif operator == 'GATE':
            self.op_gate(args[0].value)
        
        elif operator == 'SATURATE':
            self.op_saturate(args[0].value)
        
        elif operator == 'WITNESS':
            self.op_witness()
        
        elif operator == 'HALT':
            self.op_halt()
    
    def op_push(self, value: Any):
        """PUSH operator - add symbol to stack"""
        if len(self.stack) >= self.config.max_stack_depth:
            raise StackOverflowError(
                f"Stack overflow (max depth: {self.config.max_stack_depth})"
            )
        
        self.stack.append(str(value))
    
    def op_invert(self):
        """INVERT operator - reverse stack"""
        self.stack.reverse()
    
    def op_bind(self, key: Any, value: Any):
        """BIND operator - create association"""
        if len(self.bindings) >= self.config.max_bindings:
            raise BindingsOverflowError(
                f"Bindings overflow (max: {self.config.max_bindings})"
            )
        
        self.bindings[str(key)] = str(value)
    
    def op_release(self, key: Any):
        """RELEASE operator - remove binding"""
        self.bindings.pop(str(key), None)
    
    def op_gate(self, condition: str):
        """GATE operator - conditional execution"""
        if not self.evaluate_condition(condition):
            raise BreakBlock()
    
    def op_saturate(self, operations: List[Operation]):
        """SATURATE operator - repeat until fixed point"""
        iteration = 0
        
        while iteration < self.config.max_saturate_iterations:
            # Snapshot state before
            state_before = self.snapshot_state()
            
            # Execute block
            try:
                for operation in operations:
                    self.execute_operation(operation)
            except BreakBlock:
                # GATE caused early exit
                break
            
            # Snapshot state after
            state_after = self.snapshot_state()
            
            # Check fixed point
            if self.states_equal(state_before, state_after):
                break
            
            iteration += 1
        
        if iteration >= self.config.max_saturate_iterations:
            raise CycleLimitError(
                f"SATURATE exceeded {self.config.max_saturate_iterations} iterations"
            )
    
    def op_witness(self):
        """WITNESS operator - record checkpoint"""
        if self.config.trace_enabled:
            self.trace.append({
                'phase': self.current_phase_name,
                'operation': self.operation_counter,
                'stack': self.stack.copy(),
                'bindings': self.bindings.copy()
            })
    
    def op_halt(self):
        """HALT operator - terminate execution"""
        self.halted = True
        raise HaltProgram()
    
    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a GATE condition"""
        condition = condition.strip()
        
        # Parse depth comparisons
        if condition.startswith('depth'):
            parts = condition.split()
            if len(parts) != 3:
                raise ConditionError(f"Invalid condition: {condition}")
            
            operator = parts[1]
            try:
                value = int(parts[2])
            except ValueError:
                raise ConditionError(f"Invalid numeric value in condition: {condition}")
            
            depth = len(self.stack)
            
            if operator == '<':
                return depth < value
            elif operator == '>':
                return depth > value
            elif operator == '==':
                return depth == value
            else:
                raise ConditionError(f"Invalid operator in condition: {operator}")
        
        # Parse bound/unbound checks
        if condition.startswith('bound'):
            key = condition.split()[1] if len(condition.split()) > 1 else ''
            return key in self.bindings
        
        if condition.startswith('unbound'):
            key = condition.split()[1] if len(condition.split()) > 1 else ''
            return key not in self.bindings
        
        raise ConditionError(f"Unknown condition type: {condition}")
    
    def snapshot_state(self) -> Dict[str, Any]:
        """Create deep copy of current state"""
        return {
            'stack': deepcopy(self.stack),
            'bindings': deepcopy(self.bindings)
        }
    
    def states_equal(self, state1: Dict, state2: Dict) -> bool:
        """Compare two states for equality"""
        return (
            state1['stack'] == state2['stack'] and
            state1['bindings'] == state2['bindings']
        )
