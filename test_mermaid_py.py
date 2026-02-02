#!/usr/bin/env python3
"""
Test suite for Mermaid diagram generation using mermaid-py library.
This library requires pre-built graph definitions as strings.
"""

from mermaid import Mermaid
import sys
import os


def test_sequence_diagram():
    """Test sequence diagram generation."""
    print("\n" + "=" * 80)
    print("TEST 1: Sequence Diagram (Agent Components)")
    print("=" * 80)
    
    # Build mermaid code as string
    graph_code = """sequenceDiagram
    participant Agent as AgentSupervisor
    participant Config as ConfigManager
    participant Docker as DockerManager
    participant State as Shared State
    participant Resource as ResourceController

    Agent->>Config: init_config()
    activate Config
    Config-->>Agent: config loaded
    deactivate Config
    
    Agent->>Docker: start containers
    activate Docker
    Docker->>State: update status
    activate State
    State-->>Docker: ack
    deactivate State
    Docker-->>Agent: ready
    deactivate Docker
    
    Agent->>Resource: start monitoring
    activate Resource
    Resource->>State: register listener
    Resource-->>Agent: monitoring started
"""
    
    mmd = Mermaid(graph_code)
    print("\nGenerated Mermaid code:")
    print(graph_code)
    print("\n✓ Sequence diagram test passed!")
    return graph_code, "sequence_diagram"


def test_flowchart():
    """Test flowchart generation."""
    print("\n" + "=" * 80)
    print("TEST 2: Flowchart (Agent Lifecycle)")
    print("=" * 80)
    
    graph_code = """flowchart TD
    A["🚀 Start Agent"] --> B{"Check Git<br/>Branch"}
    B -->|dev branch| C["⚙️  Initialize Config"]
    B -->|wrong branch| G["❌ Error: Wrong Branch"]
    
    C --> D["🐳 Start Docker<br/>Containers"]
    D -->|success| E["🔄 Spawn Manager<br/>Processes"]
    D -->|failure| G
    
    E --> F["👁️  Monitor Processes<br/>& Resources"]
    
    F -->|running| F
    F -->|interrupt| H["🛑 Graceful<br/>Shutdown"]
    F -->|error| H
    
    H --> I["🏁 End"]
    G --> I
"""
    
    mmd = Mermaid(graph_code)
    print("\nGenerated Mermaid code:")
    print(graph_code)
    print("\n✓ Flowchart test passed!")
    return graph_code, "flowchart"


def test_class_diagram():
    """Test class diagram generation."""
    print("\n" + "=" * 80)
    print("TEST 3: Class Diagram (Component Architecture)")
    print("=" * 80)
    
    graph_code = """classDiagram
    class BaseComponent {
        #dict shared_state
        #ConfigManager config
        #Event shutdown_event
        #Logger logger
        +get_config(key, default) dict
        +update_shared_state(key, value)* void
        +is_shutdown_requested()* bool
    }
    
    class ResourceController {
        -int throttling_level
        -dict thresholds
        +run() void
        +check_resources() void
        +apply_throttling() void
    }
    
    class DockerManager {
        -list container_names
        -dict containers
        +start_services() bool
        +stop_services() bool
        +health_check() bool
    }
    
    class MetricsServer {
        -int port
        -dict metrics
        +start() void
        +collect_metrics() dict
        +get_metrics() dict
    }
    
    class ConnectivityAsync {
        -dict status
        +check_aws() bool
        +check_redis() bool
        +check_pipeline() bool
    }
    
    ResourceController --|> BaseComponent: inherits
    DockerManager --|> BaseComponent: inherits
    MetricsServer --|> BaseComponent: inherits
    ConnectivityAsync --|> BaseComponent: inherits
    ResourceController --> DockerManager: manages
    MetricsServer --> ConnectivityAsync: uses
"""
    
    mmd = Mermaid(graph_code)
    print("\nGenerated Mermaid code:")
    print(graph_code)
    print("\n✓ Class diagram test passed!")
    return graph_code, "class_diagram"


def test_state_diagram():
    """Test state diagram generation."""
    print("\n" + "=" * 80)
    print("TEST 4: State Diagram (Agent State Machine)")
    print("=" * 80)
    
    graph_code = """stateDiagram-v2
    [*] --> Initializing
    
    Initializing: Checking config & dependencies
    Initializing --> DockerStarting: config_ready
    Initializing --> Error: config_invalid
    
    DockerStarting: Spinning up containers
    DockerStarting --> Running: docker_healthy
    DockerStarting --> Error: docker_failed
    
    Running: Monitoring processes
    Running --> Throttling: high_cpu | high_mem
    Running --> ShuttingDown: interrupt | error
    
    Throttling: Resource limit exceeded
    Throttling --> Running: normal_resources
    Throttling --> ShuttingDown: interrupt | error
    
    ShuttingDown: Graceful shutdown
    ShuttingDown --> Stopped: shutdown_complete
    
    Error: Error occurred
    Error --> Stopped
    
    Stopped --> [*]
"""
    
    mmd = Mermaid(graph_code)
    print("\nGenerated Mermaid code:")
    print(graph_code)
    print("\n✓ State diagram test passed!")
    return graph_code, "state_diagram"


def test_graph_diagram():
    """Test simple graph/relationship diagram."""
    print("\n" + "=" * 80)
    print("TEST 5: Graph Diagram (Data Flow)")
    print("=" * 80)
    
    graph_code = """graph LR
    Suricata["Suricata IDS"] -->|eve.json| RAM["/mnt/ram_logs"]
    RAM -->|tail| Vector["Vector Agent"]
    Vector -->|ECS Transform| Redis["Redis Queue"]
    Vector -->|Also sends to| AWS["AWS OpenSearch"]
    Redis -->|consume| Dashboard["Grafana Dashboard"]
    AWS -->|query| Dashboard
    
    Prom["Prometheus"] -->|metrics| Dashboard
    Docker["Docker Containers"] -->|metrics| Prom
    Host["Host System"] -->|metrics| Prom
    
    style Suricata fill:#ff9999
    style Vector fill:#99ccff
    style Dashboard fill:#99ff99
    style AWS fill:#ffcc99
"""
    
    mmd = Mermaid(graph_code)
    print("\nGenerated Mermaid code:")
    print(graph_code)
    print("\n✓ Graph diagram test passed!")
    return graph_code, "graph_diagram"


def save_diagrams(diagrams_list):
    """Save all generated diagrams to files."""
    print("\n" + "=" * 80)
    print("SAVING DIAGRAMS TO FILES")
    print("=" * 80)
    
    output_dir = "/home/tor/Downloads/oi/mermaid_generated"
    os.makedirs(output_dir, exist_ok=True)
    
    for code, name in diagrams_list:
        filename = os.path.join(output_dir, f"{name}.mmd")
        with open(filename, 'w') as f:
            f.write(code)
        print(f"✓ Saved: {filename}")
        print(f"  Size: {len(code)} bytes")
    
    return output_dir


def main():
    """Run all tests."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "MERMAID-PY LIBRARY COMPREHENSIVE TEST SUITE" + " " * 17 + "║")
    print("╚" + "=" * 78 + "╝")
    
    diagrams = []
    
    try:
        diagrams.append(test_sequence_diagram())
        diagrams.append(test_flowchart())
        diagrams.append(test_class_diagram())
        diagrams.append(test_state_diagram())
        diagrams.append(test_graph_diagram())
        
        output_dir = save_diagrams(diagrams)
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY & RESULTS")
        print("=" * 80)
        print(f"✓ All {len(diagrams)} tests passed successfully!")
        print(f"✓ Generated {len(diagrams)} diagram types")
        print(f"✓ Saved to: {output_dir}/")
        
        print("\nGenerated files:")
        for code, name in diagrams:
            print(f"  • {name}.mmd")
        
        print("\nNext steps to render diagrams:")
        print(f"  1. Install mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
        print(f"  2. Render PNG: mmdc -i {output_dir}/*.mmd -o {output_dir}/")
        print(f"  3. View online: https://mermaid.live")
        print(f"  4. Use in VS Code: Install 'Markdown Preview Mermaid Support' extension")
        
        print("\nLibrary information:")
        print("  • Package: mermaid-py")
        print("  • GitHub: https://github.com/Dr-ZHUIM/mermaid-py")
        print("  • Use case: Generate Mermaid diagrams programmatically in Python")
        print("  • Primary method: Create diagram as string, pass to Mermaid()")
        print("  • Can export to: PNG, SVG (via to_png(), to_svg() methods)")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
