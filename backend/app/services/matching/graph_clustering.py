import logging
import networkx as nx
from sqlalchemy.orm import Session
from typing import List, Set

from app.db.models.source_record import SourceRecord
from app.db.models.identity_edge import IdentityEdge

logger = logging.getLogger(__name__)

def run_graph_clustering(db: Session) -> List[Set[int]]:
    """
    Builds an undirected graph of all SourceRecords connected by AUTO_MERGED edges.
    Extracts connected components (clusters).
    Returns a list of clusters, where each cluster is a set of SourceRecord IDs.
    """
    logger.info("Starting Phase 2 - Step 4: Graph Clustering")
    
    G = nx.Graph()
    
    # Add all source records as nodes so singletons remain as isolated clusters of size 1
    records = db.query(SourceRecord.id).all()
    for (r_id,) in records:
        G.add_node(r_id)
        
    # Add edges that meet auto-merge criteria
    edges = db.query(IdentityEdge).filter(
        IdentityEdge.match_phase.in_([
            "deterministic", 
            "probabilistic_auto_merged", 
            "semantic_auto_merged"
        ])
    ).all()
    
    for edge in edges:
        G.add_edge(edge.source_record_a_id, edge.source_record_b_id)
        
    # Extract connected components
    clusters = list(nx.connected_components(G))
    logger.info(f"Graph clustering complete. Found {len(clusters)} unique identity clusters.")
    
    return clusters
