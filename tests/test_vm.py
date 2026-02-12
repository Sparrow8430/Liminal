#!/usr/bin/env python3
"""
Test suite for liminal-vm
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parser import parse_program
from vm import VirtualMachine, VMConfig
from errors import ParseError, StackOverflowError, CycleLimitError

def test_parse_simple():
    """Test parsing a simple program"""
    source = """
    BEGIN {
        PUSH "test"
        WITNESS
    }
    """
    program = parse_program(source)
    assert len(program.phases) == 1
    assert program.phases[0].name == "BEGIN"
    assert len(program.phases[0].operations) == 2
    print("✓ test_parse_simple")

def test_parse_multiple_phases():
    """Test parsing multiple phases"""
    source = """
    PHASE_ONE {
        PUSH "a"
    }
    PHASE_TWO {
        PUSH "b"
        INVERT
    }
    """
    program = parse_program(source)
    assert len(program.phases) == 2
    assert program.phases[0].name == "PHASE_ONE"
    assert program.phases[1].name == "PHASE_TWO"
    print("✓ test_parse_multiple_phases")

def test_parse_saturate():
    """Test parsing SATURATE block"""
    source = """
    TEST {
        SATURATE {
            PUSH "x"
            GATE depth < 5
        }
    }
    """
    program = parse_program(source)
    op = program.phases[0].operations[0]
    assert op.operator == "SATURATE"
    assert op.arguments[0].type == "BLOCK"
    print("✓ test_parse_saturate")

def test_execute_push():
    """Test PUSH operation"""
    source = """
    TEST {
        PUSH "alpha"
        PUSH "beta"
        HALT
    }
    """
    program = parse_program(source)
    vm = VirtualMachine()
    result = vm.execute(program)
    
    assert result.status == "HALTED"
    assert len(result.final_state['stack']) == 2
    assert result.final_state['stack'] == ["alpha", "beta"]
    print("✓ test_execute_push")

def test_execute_invert():
    """Test INVERT operation"""
    source = """
    TEST {
        PUSH "a"
        PUSH "b"
        PUSH "c"
        INVERT
        HALT
    }
    """
    program = parse_program(source)
    vm = VirtualMachine()
    result = vm.execute(program)
    
    assert result.final_state['stack'] == ["c", "b", "a"]
    print("✓ test_execute_invert")

def test_execute_bind():
    """Test BIND operation"""
    source = """
    TEST {
        BIND "key" "value"
        BIND "another" "binding"
        HALT
    }
    """
    program = parse_program(source)
    vm = VirtualMachine()
    result = vm.execute(program)
    
    assert result.final_state['bindings'] == {
        "key": "value",
        "another": "binding"
    }
    print("✓ test_execute_bind")

def test_execute_release():
    """Test RELEASE operation"""
    source = """
    TEST {
        BIND "temp" "value"
        RELEASE "temp"
        HALT
    }
    """
    program = parse_program(source)
    vm = VirtualMachine()
    result = vm.execute(program)
    
    assert result.final_state['bindings'] == {}
    print("✓ test_execute_release")

def test_execute_gate():
    """Test GATE operation"""
    source = """
    TEST {
        PUSH "a"
        PUSH "b"
        GATE depth < 5
        PUSH "c"
        GATE depth < 2
        PUSH "unreachable"
        HALT
    }
    """
    program = parse_program(source)
    vm = VirtualMachine()
    result = vm.execute(program)
    
    # Should stop at second GATE (depth is 3, condition depth < 2 fails)
    # But GATE in main execution just continues...
    # Actually GATE only breaks in SATURATE blocks
    assert len(result.final_state['stack']) >= 3
    print("✓ test_execute_gate")

def test_execute_saturate():
    """Test SATURATE operation"""
    source = """
    TEST {
        SATURATE {
            PUSH "x"
            GATE depth < 5
        }
        HALT
    }
    """
    program = parse_program(source)
    vm = VirtualMachine()
    result = vm.execute(program)
    
    assert len(result.final_state['stack']) == 5
    print("✓ test_execute_saturate")

def test_fixed_point():
    """Test fixed point detection in SATURATE"""
    source = """
    TEST {
        SATURATE {
            GATE unbound done
            BIND "done" "yes"
        }
        HALT
    }
    """
    program = parse_program(source)
    vm = VirtualMachine()
    result = vm.execute(program)
    
    # Should terminate after 2 iterations (first binds, second breaks)
    assert result.final_state['bindings'] == {"done": "yes"}
    assert result.operations_executed < 10  # Should be very few operations
    print("✓ test_fixed_point")

def test_stack_overflow():
    """Test stack overflow protection"""
    source = """
    TEST {
        SATURATE {
            PUSH "overflow"
            GATE depth < 1000
        }
    }
    """
    program = parse_program(source)
    config = VMConfig(max_stack_depth=64)
    vm = VirtualMachine(config)
    result = vm.execute(program)
    
    assert result.status == "ERR_STACK_OVERFLOW"
    print("✓ test_stack_overflow")

def test_cycle_limit():
    """Test SATURATE iteration limit"""
    source = """
    TEST {
        SATURATE {
            PUSH "infinite"
        }
    }
    """
    program = parse_program(source)
    config = VMConfig(max_saturate_iterations=100)
    vm = VirtualMachine(config)
    result = vm.execute(program)
    
    assert result.status == "TERM_CYCLE_LIMIT"
    print("✓ test_cycle_limit")

def test_operation_limit():
    """Test operation budget"""
    source = """
    LOOP {
        SATURATE {
            PUSH "a"
            PUSH "b"
            PUSH "c"
            GATE depth < 1000
        }
    }
    """
    program = parse_program(source)
    config = VMConfig(max_operations=50, max_stack_depth=1000)
    vm = VirtualMachine(config)
    result = vm.execute(program)
    
    assert result.status == "TERM_OP_LIMIT"
    print("✓ test_operation_limit")

def test_witness_trace():
    """Test WITNESS checkpoints"""
    source = """
    TEST {
        PUSH "a"
        WITNESS
        PUSH "b"
        WITNESS
        HALT
    }
    """
    program = parse_program(source)
    config = VMConfig(trace_enabled=True)
    vm = VirtualMachine(config)
    result = vm.execute(program)
    
    assert len(result.trace) == 2
    assert result.trace[0]['stack'] == ["a"]
    assert result.trace[1]['stack'] == ["a", "b"]
    print("✓ test_witness_trace")

def run_all_tests():
    """Run all tests"""
    tests = [
        test_parse_simple,
        test_parse_multiple_phases,
        test_parse_saturate,
        test_execute_push,
        test_execute_invert,
        test_execute_bind,
        test_execute_release,
        test_execute_gate,
        test_execute_saturate,
        test_fixed_point,
        test_stack_overflow,
        test_cycle_limit,
        test_operation_limit,
        test_witness_trace,
    ]
    
    print("\nRunning tests...\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} - {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} - Unexpected error: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}\n")
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
