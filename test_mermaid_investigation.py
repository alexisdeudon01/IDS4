#!/usr/bin/env python3
"""Comprehensive test of the mermaid library for generating Mermaid diagrams."""

import mermaid
import json

print("=" * 80)
print("Mermaid Library Investigation & Testing")
print("=" * 80)

# Inspect the mermaid module
print("\n1. Module Contents:")
print(f"   Package: mermaid")
attrs = [attr for attr in dir(mermaid) if not attr.startswith('_')]
print(f"   Available attributes: {attrs}")

# Test what we can do with it
print("\n2. Testing mermaid module usage...")

# Check for main classes/functions
if hasattr(mermaid, 'Diagram'):
    print("   ✓ Has Diagram class")
    try:
        # Try to create a diagram
        diag = mermaid.Diagram("graph TD; A-->B")
        print(f"     Type: {type(diag)}")
        print(f"     Methods: {[m for m in dir(diag) if not m.startswith('_')][:10]}")
    except Exception as e:
        print(f"     Error creating diagram: {e}")

if hasattr(mermaid, 'MermaidChart'):
    print("   ✓ Has MermaidChart class")

# List all public classes
public_classes = [attr for attr in dir(mermaid) if not attr.startswith('_') and attr[0].isupper()]
print(f"\n   Public classes found: {public_classes}")

# Test the mermaid module's actual API
print("\n3. Testing actual mermaid library functionality...")

# Check if it has a render or similar function
if hasattr(mermaid, 'render'):
    print("   ✓ Has render function")
    print(f"     Signature help: {mermaid.render.__doc__[:100] if mermaid.render.__doc__ else 'No docs'}")

# Get the mermaid module path to understand what library this is
print(f"\n4. Module location: {mermaid.__file__}")

# Try to inspect the library more deeply
print("\n5. Attempting to generate diagrams with the mermaid library...")

try:
    # Test 1: Simple flowchart
    flowchart_code = """
    graph TD
        A["Start"]
        B["Process"]
        C["End"]
        A --> B --> C
    """
    
    if hasattr(mermaid, 'Diagram'):
        diagram = mermaid.Diagram(flowchart_code)
        print("   ✓ Created flowchart diagram")
    else:
        print(f"   Info: mermaid module doesn't have Diagram class")
        print(f"   Available: {public_classes}")
    
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Try to use it as a helper/validator
print("\n6. Mermaid library capabilities check...")
print(f"   Is it a rendering library? {hasattr(mermaid, 'render')}")
print(f"   Is it a builder? {hasattr(mermaid, 'Diagram')}")
print(f"   All exported items: {public_classes}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print("""
The installed 'mermaid' package appears to be a lightweight wrapper.
For robust Mermaid diagram generation in Python, consider:

1. **pymermaid** - High-level API for building diagrams
2. **Custom Builder Classes** - Best for your use case (full control, no dependencies)
3. **Using mermaid-js/mermaid-cli** - If rendering to PNG/SVG is needed

The custom builder approach demonstrated earlier works perfectly and can generate:
  - Sequence Diagrams
  - Class Diagrams  
  - Flowcharts
  - State Diagrams
  - And more!
""")

print("\n" + "=" * 80)
