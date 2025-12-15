"""
System Design Diagram Renderer
Generates Mermaid diagrams from structured system design text
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemComponent:
    """A component in the system design"""
    name: str
    type: str  # service, database, queue, cache, api, worker
    connections: List[str]


class DiagramRenderer:
    """
    Renders system design as Mermaid diagrams
    """
    
    def __init__(self):
        self.components: Dict[str, SystemComponent] = {}
        self.connections: List[tuple] = []
    
    def parse_design(self, design_text: str) -> str:
        """
        Parse natural language system design into Mermaid diagram
        
        Recognizes patterns like:
        - "Client connects to API Gateway"
        - "API Gateway talks to Auth Service"
        - "Service uses Postgres database"
        - "Cache with Redis"
        - "Message queue: Kafka"
        """
        lines = design_text.lower().split('\n')
        
        # Component type keywords
        db_keywords = ['database', 'postgres', 'mysql', 'mongodb', 'db']
        cache_keywords = ['cache', 'redis', 'memcached']
        queue_keywords = ['queue', 'kafka', 'rabbitmq', 'sqs', 'pubsub']
        service_keywords = ['service', 'api', 'server', 'microservice']
        worker_keywords = ['worker', 'job', 'processor']
        
        components_found = set()
        
        # Extract components
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for component mentions
            words = line.split()
            for i, word in enumerate(words):
                word_clean = word.strip('.,;:')
                
                # Database
                if any(kw in word_clean for kw in db_keywords):
                    comp_name = self._extract_component_name(words, i, 'database')
                    if comp_name:
                        components_found.add((comp_name, 'database'))
                
                # Cache
                elif any(kw in word_clean for kw in cache_keywords):
                    comp_name = self._extract_component_name(words, i, 'cache')
                    if comp_name:
                        components_found.add((comp_name, 'cache'))
                
                # Queue
                elif any(kw in word_clean for kw in queue_keywords):
                    comp_name = self._extract_component_name(words, i, 'queue')
                    if comp_name:
                        components_found.add((comp_name, 'queue'))
                
                # Worker
                elif any(kw in word_clean for kw in worker_keywords):
                    comp_name = self._extract_component_name(words, i, 'worker')
                    if comp_name:
                        components_found.add((comp_name, 'worker'))
                
                # Service/API
                elif any(kw in word_clean for kw in service_keywords):
                    comp_name = self._extract_component_name(words, i, 'service')
                    if comp_name:
                        components_found.add((comp_name, 'service'))
        
        # Always add client
        components_found.add(('Client', 'client'))
        
        # Build Mermaid diagram
        return self._generate_mermaid(list(components_found), design_text)
    
    def _extract_component_name(self, words: List[str], index: int, comp_type: str) -> Optional[str]:
        """Extract component name from word list"""
        # Try to get name before or after keyword
        name_parts = []
        
        # Look before (1-2 words)
        for i in range(max(0, index - 2), index):
            word = words[i].strip('.,;:').title()
            if word and len(word) > 2 and word not in ['the', 'a', 'an', 'to', 'from', 'with']:
                name_parts.append(word)
        
        # Add the keyword itself
        name_parts.append(words[index].strip('.,;:').title())
        
        # Look after (1 word)
        if index + 1 < len(words):
            word = words[index + 1].strip('.,;:').title()
            if word and len(word) > 2 and word not in ['the', 'a', 'an', 'to', 'from', 'with']:
                name_parts.append(word)
        
        return ' '.join(name_parts[:2]) if name_parts else None
    
    def _generate_mermaid(self, components: List[tuple], full_text: str) -> str:
        """Generate Mermaid flowchart"""
        mermaid = ["flowchart LR\n"]
        
        # Define nodes with icons
        node_defs = {}
        for name, comp_type in components:
            node_id = self._sanitize_id(name)
            
            if comp_type == 'database':
                node_defs[node_id] = f"  {node_id}[({name})]"
            elif comp_type == 'cache':
                node_defs[node_id] = f"  {node_id}[({name})]"
            elif comp_type == 'queue':
                node_defs[node_id] = f"  {node_id}>{name}]"
            elif comp_type == 'worker':
                node_defs[node_id] = f"  {node_id}[{name}]"
            elif comp_type == 'service':
                node_defs[node_id] = f"  {node_id}[{name}]"
            elif comp_type == 'client':
                node_defs[node_id] = f"  {node_id}[{name}]"
            else:
                node_defs[node_id] = f"  {node_id}[{name}]"
        
        # Infer connections from text
        connections = []
        text_lower = full_text.lower()
        
        comp_names = [name for name, _ in components]
        
        # Look for connection patterns
        connection_patterns = [
            (r'(\w+(?:\s+\w+)?)\s+(?:connects? to|talks? to|uses?|calls?|sends? to)\s+(\w+(?:\s+\w+)?)', '-->'),
            (r'(\w+(?:\s+\w+)?)\s+(?:reads? from|queries?|fetches? from)\s+(\w+(?:\s+\w+)?)', '-.->'),
            (r'(\w+(?:\s+\w+)?)\s+(?:writes? to|stores? in|saves? to)\s+(\w+(?:\s+\w+)?)', '-->'),
        ]
        
        for pattern, arrow in connection_patterns:
            matches = re.findall(pattern, text_lower)
            for source, target in matches:
                source = source.strip().title()
                target = target.strip().title()
                
                # Check if these match any component names
                source_match = self._find_matching_component(source, comp_names)
                target_match = self._find_matching_component(target, comp_names)
                
                if source_match and target_match:
                    connections.append((source_match, target_match, arrow))
        
        # Default connections if none found
        if not connections and len(components) > 1:
            # Create linear flow
            sorted_comps = sorted(components, key=lambda x: ('client', 'service', 'queue', 'worker', 'cache', 'database').index(x[1]) if x[1] in ('client', 'service', 'queue', 'worker', 'cache', 'database') else 99)
            for i in range(len(sorted_comps) - 1):
                connections.append((sorted_comps[i][0], sorted_comps[i+1][0], '-->'))
        
        # Build Mermaid
        for node_id, node_def in node_defs.items():
            mermaid.append(node_def)
        
        mermaid.append("\n")
        
        for source, target, arrow in connections:
            source_id = self._sanitize_id(source)
            target_id = self._sanitize_id(target)
            if source_id in node_defs and target_id in node_defs:
                mermaid.append(f"  {source_id} {arrow} {target_id}")
        
        # Add styling
        mermaid.append("\n")
        mermaid.append("  classDef database fill:#f9f,stroke:#333,stroke-width:2px")
        mermaid.append("  classDef cache fill:#ff9,stroke:#333,stroke-width:2px")
        mermaid.append("  classDef queue fill:#9ff,stroke:#333,stroke-width:2px")
        
        return '\n'.join(mermaid)
    
    def _sanitize_id(self, name: str) -> str:
        """Convert name to valid Mermaid ID"""
        return re.sub(r'[^a-zA-Z0-9]', '', name)
    
    def _find_matching_component(self, text: str, components: List[str]) -> Optional[str]:
        """Find component that matches text"""
        text_lower = text.lower()
        for comp in components:
            if text_lower in comp.lower() or comp.lower() in text_lower:
                return comp
        return None


def render_system_design(design_text: str) -> str:
    """
    Render system design as Mermaid diagram
    
    Example:
        design = '''
        Client connects to API Gateway
        API Gateway talks to Auth Service
        Auth Service uses Postgres database
        API Gateway also calls Core Service
        Core Service reads from Redis cache
        Core Service writes to Kafka queue
        Kafka sends messages to Worker
        '''
        
        mermaid = render_system_design(design)
        # Returns Mermaid flowchart syntax
    """
    renderer = DiagramRenderer()
    return renderer.parse_design(design_text)


def generate_mermaid_from_components(
    services: List[str],
    databases: List[str],
    caches: List[str] = None,
    queues: List[str] = None,
    workers: List[str] = None
) -> str:
    """
    Generate Mermaid diagram from explicit components
    
    Example:
        mermaid = generate_mermaid_from_components(
            services=['API Gateway', 'Auth Service', 'Core Service'],
            databases=['Postgres'],
            caches=['Redis'],
            queues=['Kafka'],
            workers=['Async Worker']
        )
    """
    mermaid = ["flowchart LR\n"]
    
    # Client
    mermaid.append("  Client[Client]")
    
    # Services
    for svc in services:
        svc_id = re.sub(r'[^a-zA-Z0-9]', '', svc)
        mermaid.append(f"  {svc_id}[{svc}]")
    
    # Databases
    for db in databases:
        db_id = re.sub(r'[^a-zA-Z0-9]', '', db)
        mermaid.append(f"  {db_id}[({db})]")
    
    # Caches
    if caches:
        for cache in caches:
            cache_id = re.sub(r'[^a-zA-Z0-9]', '', cache)
            mermaid.append(f"  {cache_id}[({cache})]")
    
    # Queues
    if queues:
        for queue in queues:
            queue_id = re.sub(r'[^a-zA-Z0-9]', '', queue)
            mermaid.append(f"  {queue_id}>{queue}]")
    
    # Workers
    if workers:
        for worker in workers:
            worker_id = re.sub(r'[^a-zA-Z0-9]', '', worker)
            mermaid.append(f"  {worker_id}[{worker}]")
    
    # Connections
    mermaid.append("\n")
    mermaid.append("  Client --> " + re.sub(r'[^a-zA-Z0-9]', '', services[0]))
    
    for i, svc in enumerate(services):
        svc_id = re.sub(r'[^a-zA-Z0-9]', '', svc)
        
        # Connect to databases
        if databases:
            db_id = re.sub(r'[^a-zA-Z0-9]', '', databases[0])
            mermaid.append(f"  {svc_id} --> {db_id}")
        
        # Connect to caches
        if caches:
            cache_id = re.sub(r'[^a-zA-Z0-9]', '', caches[0])
            mermaid.append(f"  {svc_id} -.-> {cache_id}")
        
        # Connect to queues
        if queues and i == len(services) - 1:
            queue_id = re.sub(r'[^a-zA-Z0-9]', '', queues[0])
            mermaid.append(f"  {svc_id} --> {queue_id}")
            
            # Connect queue to workers
            if workers:
                worker_id = re.sub(r'[^a-zA-Z0-9]', '', workers[0])
                mermaid.append(f"  {queue_id} --> {worker_id}")
    
    return '\n'.join(mermaid)
