# backend/long_term/retrieval.py

"""
Memory Retrieval - Enhanced contextual recall system
Retrieves relevant memories using semantic matching and ranking
"""

from typing import List, Dict, Tuple, Optional
import re
from collections import Counter


def retrieve_relevant(query: str, memories: List[tuple], top_k: int = 5, 
                     min_score: float = 0.0) -> List[dict]:
    """
    Retrieve memories relevant to the current query
    Uses enhanced keyword matching with TF-IDF weighting
    
    Args:
        query: Current user message
        memories: List of active memories
        top_k: Maximum number of memories to return
        min_score: Minimum relevance score to include
        
    Returns:
        List of relevant memory dictionaries
    """
    if not memories:
        return []
    
    query_lower = query.lower()
    query_words = _tokenize(query_lower)
    
    # Remove common stop words
    query_words = _remove_stop_words(query_words)
    
    if not query_words:
        return []
    
    scored_memories = []
    
    for mem in memories:
        mem_id = mem[0]
        mem_type = mem[1]
        content = mem[2]
        confidence = mem[3]
        created_turn = mem[4]
        last_used = mem[5]
        use_count = mem[6] if len(mem) > 6 else 1
        
        content_lower = content.lower()
        content_words = _tokenize(content_lower)
        content_words = _remove_stop_words(content_words)
        
        # Calculate relevance score
        score = _calculate_enhanced_relevance(
            query_words, content_words, confidence, 
            mem_type, use_count, query_lower, content_lower
        )
        
        if score > min_score:
            scored_memories.append({
                "id": mem_id,
                "type": mem_type,
                "content": content,
                "confidence": confidence,
                "relevance": score,
                "created_turn": created_turn,
                "last_used_turn": last_used,
                "use_count": use_count
            })
    
    # Sort by relevance, then confidence
    scored_memories.sort(key=lambda x: (x["relevance"], x["confidence"]), reverse=True)
    
    return scored_memories[:top_k]


def _tokenize(text: str) -> List[str]:
    """
    Tokenize text into words
    
    Args:
        text: Input text
        
    Returns:
        List of tokens
    """
    # Split on whitespace and punctuation
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def _remove_stop_words(words: List[str]) -> List[str]:
    """
    Remove common stop words
    
    Args:
        words: List of words
        
    Returns:
        Filtered list
    """
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
        'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'my'
    }
    
    return [w for w in words if w not in stop_words and len(w) > 2]


def _calculate_enhanced_relevance(query_words: List[str], content_words: List[str],
                                  confidence: float, mem_type: str, use_count: int,
                                  query_text: str, content_text: str) -> float:
    """
    Calculate enhanced relevance score
    
    Args:
        query_words: Query tokens
        content_words: Content tokens
        confidence: Memory confidence
        mem_type: Memory type
        use_count: How many times memory was used
        query_text: Original query text
        content_text: Original content text
        
    Returns:
        float: Relevance score
    """
    if not query_words or not content_words:
        return 0.0
    
    # 1. Word overlap score (Jaccard similarity)
    query_set = set(query_words)
    content_set = set(content_words)
    
    intersection = query_set & content_set
    union = query_set | content_set
    
    jaccard = len(intersection) / len(union) if union else 0
    
    # 2. TF-IDF weighted score
    query_counter = Counter(query_words)
    content_counter = Counter(content_words)
    
    # Calculate term frequency
    tf_score = 0
    for word in intersection:
        query_tf = query_counter[word] / len(query_words)
        content_tf = content_counter[word] / len(content_words)
        tf_score += query_tf * content_tf
    
    # 3. Exact phrase matching bonus
    phrase_bonus = 0
    if len(query_words) >= 3:
        # Check for 2-3 word phrases
        for i in range(len(query_words) - 1):
            bigram = f"{query_words[i]} {query_words[i+1]}"
            if bigram in content_text:
                phrase_bonus += 0.2
    
    # 4. Named entity matching bonus
    # Check for capitalized words (potential names, places)
    query_entities = re.findall(r'\b[A-Z][a-z]+\b', query_text)
    content_entities = re.findall(r'\b[A-Z][a-z]+\b', content_text)
    
    entity_overlap = len(set(query_entities) & set(content_entities))
    entity_bonus = entity_overlap * 0.3
    
    # 5. Memory type relevance
    type_weights = {
        "fact": 1.2,       # Facts are often directly relevant
        "preference": 1.1,
        "constraint": 1.15,
        "commitment": 0.9,
        "goal": 1.0,
        "relationship": 1.0
    }
    type_weight = type_weights.get(mem_type, 1.0)
    
    # 6. Usage frequency bonus (frequently accessed = more important)
    usage_bonus = min(0.2, use_count * 0.02)
    
    # Combine all factors
    base_score = (jaccard * 0.4 + tf_score * 0.4 + phrase_bonus + entity_bonus)
    weighted_score = base_score * type_weight * confidence
    final_score = weighted_score + usage_bonus
    
    return min(1.0, final_score)


def retrieve_by_type(memories: List[tuple], mem_type: str) -> List[dict]:
    """
    Retrieve all memories of a specific type
    
    Args:
        memories: List of active memories
        mem_type: Memory type to filter by
        
    Returns:
        List of filtered memories
    """
    filtered = []
    
    for mem in memories:
        mem_id, m_type, content, confidence, created_turn, last_used = mem[:6]
        use_count = mem[6] if len(mem) > 6 else 1
        
        if m_type == mem_type:
            filtered.append({
                "id": mem_id,
                "type": m_type,
                "content": content,
                "confidence": confidence,
                "created_turn": created_turn,
                "last_used_turn": last_used,
                "use_count": use_count
            })
    
    # Sort by confidence
    filtered.sort(key=lambda x: x["confidence"], reverse=True)
    
    return filtered


def retrieve_recent(memories: List[tuple], n: int = 5) -> List[dict]:
    """
    Retrieve N most recently used memories
    
    Args:
        memories: List of active memories
        n: Number of memories to retrieve
        
    Returns:
        List of recent memories
    """
    # Convert to dicts
    mem_dicts = []
    for mem in memories:
        mem_id, mem_type, content, confidence, created_turn, last_used = mem[:6]
        use_count = mem[6] if len(mem) > 6 else 1
        
        mem_dicts.append({
            "id": mem_id,
            "type": mem_type,
            "content": content,
            "confidence": confidence,
            "created_turn": created_turn,
            "last_used_turn": last_used,
            "use_count": use_count
        })
    
    # Sort by last_used_turn
    mem_dicts.sort(key=lambda x: x["last_used_turn"], reverse=True)
    
    return mem_dicts[:n]


def get_user_name(memories: List[tuple]) -> str:
    """
    Extract user's name from fact memories
    
    Args:
        memories: List of active memories
        
    Returns:
        str: User's name or "User"
    """
    for mem in memories:
        _, mem_type, content, _, _, _ = mem[:6]
        
        if mem_type == "fact" and "my name is" in content.lower():
            # Extract name
            match = re.search(r"my name is\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", content, re.IGNORECASE)
            if match:
                name = match.group(1)
                return name.strip()
        
        # Also check "I am [Name]" pattern
        if mem_type == "fact" and re.search(r"i(?:'m| am)\s+([A-Z][a-z]+)", content):
            match = re.search(r"i(?:'m| am)\s+([A-Z][a-z]+)", content)
            if match:
                potential_name = match.group(1)
                # Verify it's likely a name (capitalized, not a common word)
                if potential_name not in ["Going", "Working", "Living", "From"]:
                    return potential_name
    
    return "User"


def get_user_preferences(memories: List[tuple], category: Optional[str] = None) -> List[dict]:
    """
    Get user preferences, optionally filtered by category
    
    Args:
        memories: List of active memories
        category: Optional category to filter (e.g., "food", "time", "communication")
        
    Returns:
        List of preference memories
    """
    preferences = retrieve_by_type(memories, "preference")
    
    if category:
        # Simple category filtering
        filtered = []
        for pref in preferences:
            content_lower = pref["content"].lower()
            if category.lower() in content_lower:
                filtered.append(pref)
        return filtered
    
    return preferences


def get_user_constraints(memories: List[tuple]) -> List[dict]:
    """
    Get user constraints/boundaries
    
    Args:
        memories: List of active memories
        
    Returns:
        List of constraint memories
    """
    return retrieve_by_type(memories, "constraint")


def get_commitments(memories: List[tuple]) -> List[dict]:
    """
    Get pending commitments/tasks
    
    Args:
        memories: List of active memories
        
    Returns:
        List of commitment memories
    """
    commitments = retrieve_by_type(memories, "commitment")
    
    # Sort by recency (most recent first)
    commitments.sort(key=lambda x: x["last_used_turn"], reverse=True)
    
    return commitments


def search_memories(memories: List[tuple], search_term: str) -> List[dict]:
    """
    Search memories by content
    
    Args:
        memories: List of active memories
        search_term: Term to search for
        
    Returns:
        List of matching memories
    """
    search_lower = search_term.lower()
    results = []
    
    for mem in memories:
        mem_id, mem_type, content, confidence, created_turn, last_used = mem[:6]
        use_count = mem[6] if len(mem) > 6 else 1
        
        if search_lower in content.lower():
            results.append({
                "id": mem_id,
                "type": mem_type,
                "content": content,
                "confidence": confidence,
                "created_turn": created_turn,
                "last_used_turn": last_used,
                "use_count": use_count
            })
    
    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    return results


def get_memory_context_summary(memories: List[tuple]) -> Dict[str, any]:
    """
    Get a comprehensive summary of memory context
    
    Args:
        memories: List of active memories
        
    Returns:
        Dictionary with context summary
    """
    summary = {
        "user_name": get_user_name(memories),
        "total_memories": len(memories),
        "preferences": len(retrieve_by_type(memories, "preference")),
        "facts": len(retrieve_by_type(memories, "fact")),
        "constraints": len(retrieve_by_type(memories, "constraint")),
        "commitments": len(retrieve_by_type(memories, "commitment")),
        "recent_memories": [m["content"] for m in retrieve_recent(memories, 3)]
    }
    
    return summary
