#!/usr/bin/env python3
"""
Comprehensive test suite for pymermaid library.
This demonstrates how to generate various Mermaid diagrams programmatically.
"""

import sys
from pymermaid import SequenceDiagram, FlowChart, ClassDiagram, StateDiagram

def test_sequence_diagram():
    """Test sequence diagram generation."""
    print("\n" + "=" * 80)
    print("TEST 1: Sequence Diagram")
    print("=" * 80)
    
    seq = SequenceDiagram()
    seq.add_participant("Agent", "AgentSupervisor")
    seq.add_participant("Config", "ConfigManager")
    seq.add_participant("Resource", "ResourceController")
    seq.add_participant("Docker", "DockerManager")
    seq.add_participant("State", "Shared State")
    
    seq.add_message("Agent", "Config", "init_config")
    seq.add_message("Agent", "Docker", "init_docker")
    seq.add_message("Docker", "State", "update docker_status")
    seq.add_message("Agent", "Resource", "start ResourceController")
    seq.add_message("Resource", "State", "update cpu_usage")
    seq.add_return("Config", "Agent", "config loaded")
    
    mermaid_code = str(seq)
    print("\nGenerated Mermaid code:")
    print(mermaid_code)
    print("\n✓ Sequence diagram test passed!")
    return mermaid_code


def test_flowchart():
    """Test flowchart generation."""
    print("\n" + "=" * 80)
    print("TEST 2: Flowchart")
    print("=" * 80)
    
    fc = FlowChart()
    
    # Create nodes
    fc.add_statement("start", "Start Agent", shape="circle")
    fc.add_statement("check_git", "Check Git Branch", shape="diamond")
    fc.add_statement("init_config", "Initialize Config", shape="rectangle")
    fc.add_statement("start_docker", "Start Docker", shape="rectangle")
    fc.add_statement("spawn_managers", "Spawn Managers", shape="rectangle")
    fc.add_statement("monitor", "Monitor Processes", shape="rectangle")
    fc.add_statement("shutdown", "Graceful Shutdown", shape="rectangle")
    fc.add_statement("end", "End", shape="circle")
    
    # Add connections
    fc.add_link("start", "check_git")
    fc.add_link("check_git", "init_config", label="yes")
    fc.add_link("check_git", "end", label="no (wrong branch)")
    fc.add_link("init_config", "start_docker")
    fc.add_link("start_docker", "spawn_managers")
    fc.add_link("spawn_managers", "monitor")
    fc.add_link("monitor", "shutdown", label="interrupt")
    fc.add_link("shutdown", "end")
    
    mermaid_code = str(fc)
    print("\nGenerated Mermaid code:")
    print(mermaid_code)
    print("\n✓ Flowchart test passed!")
    return mermaid_code


def test_class_diagram():
    """Test class diagram generation."""
    print("\n" + "=" * 80)
    print("TEST 3: Class Diagram")
    print("=" * 80)
    
    cd = ClassDiagram()
    
    # Add base class
    cd.add_class("BaseComponent")
    cd.add_property("BaseComponent", "shared_state", "dict")
    cd.add_property("BaseComponent", "config", "ConfigManager")
    cd.add_method("BaseComponent", "get_config(key, default)")
    cd.add_method("BaseComponent", "update_shared_state(key, value)")
    
    # Add derived classes
    cd.add_class("ResourceController")
    cd.add_property("ResourceController", "throttling_level", "int")
    cd.add_method("ResourceController", "run()")
    cd.add_method("ResourceController", "check_resources()")
    
    cd.add_class("MetricsServer")
    cd.add_property("MetricsServer", "port", "int")
    cd.add_method("MetricsServer", "start()")
    cd.add_method("MetricsServer", "collect_metrics()")
    
    # Add relationships
    cd.add_relationship("ResourceController", "BaseComponent", "inherits")
    cd.add_relationship("MetricsServer", "BaseComponent", "inherits")
    cd.add_relationship("ResourceController", "MetricsServer", "uses")
    
    mermaid_code = str(cd)
    print("\nGenerated Mermaid code:")
    print(mermaid_code)
    print("\n✓ Class diagram test passed!")
    return mermaid_code


def test_state_diagram():
    """Test state diagram generation."""
    print("\n" + "=" * 80)
    print("TEST 4: State Diagram")
    print("=" * 80)
    
    sd = StateDiagram()
    
    # Add states
    sd.add_state("Initializing", "Checking config & dependencies")
    sd.add_state("DockerStarting", "Spinning up containers")
    sd.add_state("Running", "Agent monitoring processes")
    sd.add_state("Throttling", "Resource limit exceeded")
    sd.add_state("Shutting Down", "Graceful shutdown in progress")
    sd.add_state("Stopped", "Agent stopped")
    
    # Add transitions
    sd.add_transition("Initializing", "DockerStarting", "config_ready")
    sd.add_transition("DockerStarting", "Running", "docker_healthy")
    sd.add_transition("Running", "Throttling", "high_resource_usage")
    sd.add_transition("Throttling", "Running", "resources_normal")
    sd.add_transition("Running", "Shutting Down", "interrupt")
    sd.add_transition("Throttling", "Shutting Down", "interrupt")
    sd.add_transition("Shutting Down", "Stopped", "shutdown_complete")
    
    mermaid_code = str(sd)
    print("\nGenerated Mermaid code:")
    print(mermaid_code)
    print("\n✓ State diagram test passed!")
    return mermaid_code


def save_diagrams(diagrams_dict):
    """Save all generated diagrams to files."""
    print("\n" + "=" * 80)
    print("SAVING DIAGRAMS")
    print("=" * 80)
    
    import os
    output_dir = "/home/tor/Downloads/oi/mermaid_generated"
    os.makedirs(output_dir, exist_ok=True)
    
    for name, code in diagrams_dict.items():
        filename = os.path.join(output_dir, f"{name}.mmd")
        with open(filename, 'w') as f:
            f.write(code)
        print(f"✓ Saved: {filename}")


def main():
    """Run all tests."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PYMERMAID LIBRARY TEST SUITE" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    
    diagrams = {}
    
    try:
        diagrams["sequence_diagram"] = test_sequence_diagram()
        diagrams["flowchart"] = test_flowchart()
        diagrams["class_diagram"] = test_class_diagram()
        diagrams["state_diagram"] = test_state_diagram()
        
        save_diagrams(diagrams)
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("✓ All tests passed successfully!")
        print(f"✓ Generated {len(diagrams)} diagram types")
        print("\nDiagrams can be rendered using:")
        print("  - mermaid-cli: mmdc -i file.mmd -o file.png")
        print("  - Online: https://mermaid.live")
        print("  - VS Code: Markdown Preview Mermaid Support extension")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
