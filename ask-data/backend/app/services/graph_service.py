from __future__ import annotations

from app.db.connection import run_query

_SCHEMA = "cai_sdx_se_indonesia"
_REL_TABLE = f"{_SCHEMA}.customer_relationships"
_CUST_TABLE = f"{_SCHEMA}.customer_dormant_segment"


def get_risk_network(customer_id: str, hop_depth: int = 2) -> dict:
    """
    BFS traversal up to hop_depth hops from customer_id.
    Returns nodes (customers) and edges (relationships).
    """
    visited: set[str] = {customer_id}
    frontier: set[str] = {customer_id}
    all_edges: list[dict] = []

    for _ in range(hop_depth):
        if not frontier:
            break

        ids_sql = ", ".join(f"'{cid}'" for cid in frontier)
        edge_rows = run_query(f"""
            SELECT customer_id, related_customer_id, relationship_type, risk_weight, is_active
            FROM {_REL_TABLE}
            WHERE is_active = 'true'
              AND (customer_id IN ({ids_sql}) OR related_customer_id IN ({ids_sql}))
        """)

        next_frontier: set[str] = set()
        for row in edge_rows:
            a, b = row["customer_id"], row["related_customer_id"]
            all_edges.append(row)
            for node in (a, b):
                if node not in visited:
                    visited.add(node)
                    next_frontier.add(node)

        frontier = next_frontier

    # Deduplicate edges by (min, max, type)
    seen_edges: set[tuple] = set()
    unique_edges = []
    for e in all_edges:
        key = (min(e["customer_id"], e["related_customer_id"]),
               max(e["customer_id"], e["related_customer_id"]),
               e["relationship_type"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    # Fetch customer details for all visited nodes
    node_ids_sql = ", ".join(f"'{cid}'" for cid in visited)
    customer_rows = run_query(f"""
        SELECT
            customer_id, customer_segment, churn_probability, churn_risk_label,
            dormant_risk_level, credit_score, credit_risk_label,
            total_deposit_balance, city, branch_name, dormant_flag
        FROM {_CUST_TABLE}
        WHERE customer_id IN ({node_ids_sql})
    """)

    nodes = []
    for c in customer_rows:
        churn = float(c["churn_probability"]) if c["churn_probability"] else 0.0
        nodes.append({
            "id":                   c["customer_id"],
            "label":                c["customer_id"],
            "segment":              c["customer_segment"],
            "churn_risk":           churn,
            "churn_risk_label":     c["churn_risk_label"],
            "dormant_risk_level":   c["dormant_risk_level"],
            "credit_score":         int(c["credit_score"]) if c["credit_score"] else 0,
            "credit_risk_label":    c["credit_risk_label"],
            "sw_amount":            int(c["total_deposit_balance"]) if c["total_deposit_balance"] else 0,
            "city":                 c["city"],
            "branch_name":          c["branch_name"],
            "is_root":              c["customer_id"] == customer_id,
            "risk_level":           _risk_level(churn),
        })

    # Compute contagion score for each node (weighted avg of connected edge risk_weights)
    contagion: dict[str, list[float]] = {n["id"]: [] for n in nodes}
    for e in unique_edges:
        w = float(e["risk_weight"])
        contagion[e["customer_id"]].append(w)
        contagion[e["related_customer_id"]].append(w)

    for node in nodes:
        weights = contagion.get(node["id"], [])
        node["contagion_score"] = round(sum(weights) / len(weights), 3) if weights else 0.0

    return {
        "root_customer_id": customer_id,
        "hop_depth":        hop_depth,
        "node_count":       len(nodes),
        "edge_count":       len(unique_edges),
        "nodes":            nodes,
        "edges": [
            {
                "source":            e["customer_id"],
                "target":            e["related_customer_id"],
                "relationship_type": e["relationship_type"],
                "risk_weight":       float(e["risk_weight"]),
            }
            for e in unique_edges
        ],
    }


def _risk_level(churn: float) -> str:
    if churn >= 0.75:
        return "critical"
    if churn >= 0.60:
        return "high"
    if churn >= 0.35:
        return "medium"
    return "low"
