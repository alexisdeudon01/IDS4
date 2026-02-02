#!/usr/bin/env python3
"""Test script to evaluate different Mermaid-generating libraries."""

print("=" * 80)
print("Testing Mermaid Generation Libraries")
print("=" * 80)

# Test 1: pymermaid
print("\n1. Testing pymermaid...")
try:
    import pymermaid
    print(f"   ✓ pymermaid installed (version: {pymermaid.__version__ if hasattr(pymermaid, '__version__') else 'unknown'})")
    
    # Try to generate a simple diagram
    diagram = pymermaid.SequenceDiagram()
    print("   ✓ Successfully created SequenceDiagram")
except ImportError as e:
    print(f"   ✗ pymermaid not installed: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: mermaid
print("\n2. Testing mermaid...")
try:
    import mermaid
    print(f"   ✓ mermaid installed")
    print(f"   Available: {dir(mermaid)[:5]}...")
except ImportError as e:
    print(f"   ✗ mermaid not installed: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: diagrams
print("\n3. Testing diagrams...")
try:
    from diagrams import Diagram
    print(f"   ✓ diagrams installed")
    print("   Note: diagrams is for infrastructure/architecture diagrams")
except ImportError as e:
    print(f"   ✗ diagrams not installed: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: eralchemy2
print("\n4. Testing eralchemy2...")
try:
    import eralchemy
    print(f"   ✓ eralchemy installed")
except ImportError as e:
    print(f"   ✗ eralchemy not installed: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Trying a simple custom builder
print("\n5. Testing custom Mermaid builder approach...")
try:
    class MermaidSequenceDiagram:
        """Simple Mermaid sequence diagram generator."""
        def __init__(self, title="Sequence Diagram"):
            self.title = title
            self.lines = ["sequenceDiagram"]
            
        def add_participant(self, name, alias=None):
            """Add a participant."""
            if alias:
                self.lines.append(f"    participant {name} as {alias}")
            else:
                self.lines.append(f"    participant {name}")
            return self
        
        def add_message(self, from_actor, to_actor, message, response=False):
            """Add a message between actors."""
            arrow = "<<-" if response else "->>"
            self.lines.append(f"    {from_actor}{arrow}{to_actor}: {message}")
            return self
        
        def to_mermaid(self):
            """Generate Mermaid code."""
            return "\n".join(self.lines)
    
    # Test it
    seq = MermaidSequenceDiagram()
    seq.add_participant("Alice", "Alice")
    seq.add_participant("Bob", "Bob")
    seq.add_message("Alice", "Bob", "Hello Bob, how are you?")
    seq.add_message("Bob", "Alice", "Hi Alice, I'm good!", response=True)
    
    diagram_text = seq.to_mermaid()
    print("   ✓ Custom builder works!")
    print("\n   Generated Mermaid code:")
    print("   " + "\n   ".join(diagram_text.split("\n")))
    
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 80)
