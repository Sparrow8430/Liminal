#!/usr/bin/env python3
"""
liminal-vm - A deterministic virtual machine for symbolic state-transition scripts
"""

import sys
import json
import argparse
from pathlib import Path
from parser import parse_program
from vm import VirtualMachine, VMConfig
from errors import LiminalError

def main():
    parser = argparse.ArgumentParser(
        description='liminal-vm: Execute symbolic state-transition scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python liminal.py run program.lmn
  python liminal.py run program.lmn --trace
  python liminal.py check program.lmn
  python liminal.py run program.lmn --max-ops 50000 --max-stack 128
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Execute a program')
    run_parser.add_argument('file', type=Path, help='Path to .lmn file')
    run_parser.add_argument('--trace', action='store_true', help='Enable execution trace')
    run_parser.add_argument('--max-ops', type=int, default=100000, help='Max operations (default: 100000)')
    run_parser.add_argument('--max-stack', type=int, default=256, help='Max stack depth (default: 256)')
    run_parser.add_argument('--max-saturate', type=int, default=1000, help='Max SATURATE iterations (default: 1000)')
    run_parser.add_argument('--max-bindings', type=int, default=1024, help='Max bindings (default: 1024)')
    run_parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Validate program syntax')
    check_parser.add_argument('file', type=Path, help='Path to .lmn file')
    check_parser.add_argument('--dump-ast', action='store_true', help='Dump AST as JSON')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Read source file
    try:
        source = args.file.read_text()
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1
    
    # Parse
    try:
        ast = parse_program(source, str(args.file))
    except LiminalError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 1
    
    # Check command - just validate
    if args.command == 'check':
        print(f"✓ {args.file} is valid")
        if args.dump_ast:
            print(json.dumps(ast.to_dict(), indent=2))
        return 0
    
    # Run command - execute
    if args.command == 'run':
        config = VMConfig(
            max_operations=args.max_ops,
            max_stack_depth=args.max_stack,
            max_saturate_iterations=args.max_saturate,
            max_bindings=args.max_bindings,
            trace_enabled=args.trace
        )
        
        vm = VirtualMachine(config)
        
        try:
            result = vm.execute(ast)
            
            if args.json:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print_result(result)
            
            # Exit code based on status
            if result.status == 'COMPLETE' or result.status == 'HALTED':
                return 0
            else:
                return 1
                
        except LiminalError as e:
            print(f"Execution error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 2

def print_result(result):
    """Print execution result in human-readable format"""
    print(f"\n{'='*60}")
    print(f"Status: {result.status}")
    
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    print(f"{'='*60}")
    print(f"Phases executed: {result.phases_executed}")
    print(f"Operations executed: {result.operations_executed}")
    print(f"{'='*60}")
    
    print(f"\nFinal State:")
    print(f"  Stack depth: {len(result.final_state['stack'])}")
    print(f"  Stack: {result.final_state['stack']}")
    print(f"  Bindings: {result.final_state['bindings']}")
    
    if result.trace:
        print(f"\nTrace ({len(result.trace)} checkpoints):")
        for i, checkpoint in enumerate(result.trace, 1):
            print(f"  [{i}] Phase: {checkpoint['phase']}, Op: {checkpoint['operation']}")
            print(f"      Stack: {checkpoint['stack']}")
            print(f"      Bindings: {checkpoint['bindings']}")
    
    print(f"{'='*60}\n")

if __name__ == '__main__':
    sys.exit(main())
