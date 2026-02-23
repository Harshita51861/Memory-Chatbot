# backend/long_term/injector.py

"""
Memory Injector - Enhanced context injection
Injects relevant memories into LLM prompts with smart formatting
"""

from typing import List, Dict, Optional


def inject_memory_context(memories: List[Dict], style: str = "detailed") -> str:
    """
    Convert memories into natural language context for LLM
    
    Args:
        memories: List of relevant memory dictionaries
        style: Injection style ("detailed", "concise", "invisible")
        
    Returns:
        str: Formatted context string
    """
    if not memories:
        return ""
    
    if style == "invisible":
        return inject_invisible(memories)
    elif style == "concise":
        return inject_concise(memories)
    else:
        return inject_detailed(memories)


def inject_detailed(memories: List[Dict]) -> str:
    """
    Detailed memory injection with full context
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        str: Detailed formatted context
    """
    context_lines = [
        "=== USER MEMORY CONTEXT ===",
        "The following information has been remembered from previous conversations:",
        ""
    ]
    
    # Group by type for cleaner presentation
    by_type = _group_by_type(memories)
    
    # Priority order for types
    type_order = ["fact", "preference", "constraint", "commitment", "goal", "relationship"]
    
    for mem_type in type_order:
        if mem_type not in by_type:
            continue
        
        type_title = _get_type_title(mem_type)
        context_lines.append(f"{type_title}:")
        
        for mem in by_type[mem_type]:
            confidence_indicator = _get_confidence_indicator(mem['confidence'])
            context_lines.append(f"  {confidence_indicator} {mem['content']}")
        
        context_lines.append("")
    
    context_lines.extend([
        "INSTRUCTIONS:",
        "- Use this information naturally in your responses",
        "- Don't explicitly mention that you're using stored memories",
        "- Personalize your responses based on this context",
        "=========================",
        ""
    ])
    
    return "\n".join(context_lines)


def inject_concise(memories: List[Dict]) -> str:
    """
    Concise memory injection - just the essentials
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        str: Concise formatted context
    """
    if not memories:
        return ""
    
    context_lines = ["[User Context]"]
    
    for mem in memories[:5]:  # Top 5 only
        context_lines.append(f"• {mem['content']}")
    
    context_lines.append("[Use naturally in response]\n")
    
    return "\n".join(context_lines)


def inject_invisible(memories: List[Dict]) -> str:
    """
    Invisible injection - seamlessly integrate into system prompt
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        str: Invisible formatted context
    """
    if not memories:
        return ""
    
    # Extract key information
    facts = []
    preferences = []
    constraints = []
    
    for mem in memories:
        mem_type = mem['type']
        content = mem['content']
        
        if mem_type == "fact":
            facts.append(content)
        elif mem_type == "preference":
            preferences.append(content)
        elif mem_type == "constraint":
            constraints.append(content)
    
    parts = []
    
    if facts:
        parts.append("User facts: " + "; ".join(facts))
    
    if preferences:
        parts.append("User preferences: " + "; ".join(preferences))
    
    if constraints:
        parts.append("User constraints: " + "; ".join(constraints))
    
    return ". ".join(parts) + "."


def inject_simple(memories: List[Dict]) -> str:
    """
    Simple memory injection (just the content)
    
    Args:
        memories: List of relevant memory dictionaries
        
    Returns:
        str: Simple formatted context
    """
    if not memories:
        return ""
    
    context = "Remembered information:\n"
    for mem in memories:
        context += f"- {mem['content']}\n"
    
    return context


def inject_for_llm(memories: List[Dict], query: str = "") -> str:
    """
    Optimized injection for LLM processing
    
    Args:
        memories: List of memories
        query: Optional current query for context
        
    Returns:
        str: LLM-optimized context
    """
    if not memories:
        return ""
    
    # Sort by relevance (already done in retrieval)
    context_parts = []
    
    # Add high-confidence facts first
    facts = [m for m in memories if m['type'] == 'fact' and m['confidence'] > 0.9]
    if facts:
        fact_text = ", ".join([m['content'] for m in facts[:2]])
        context_parts.append(f"Known facts: {fact_text}")
    
    # Add relevant preferences
    preferences = [m for m in memories if m['type'] == 'preference']
    if preferences:
        pref_text = ", ".join([m['content'] for m in preferences[:2]])
        context_parts.append(f"User preferences: {pref_text}")
    
    # Add constraints
    constraints = [m for m in memories if m['type'] == 'constraint']
    if constraints:
        const_text = ", ".join([m['content'] for m in constraints[:2]])
        context_parts.append(f"User boundaries: {const_text}")
    
    if context_parts:
        return "[Context: " + ". ".join(context_parts) + "]"
    
    return ""


def get_memory_summary(memories: List[Dict]) -> Dict:
    """
    Get a summary of current memory state
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        dict: Summary statistics
    """
    if not memories:
        return {
            "total": 0,
            "by_type": {},
            "avg_confidence": 0,
            "high_confidence_count": 0
        }
    
    by_type = _group_by_type(memories)
    high_confidence = len([m for m in memories if m["confidence"] > 0.9])
    
    return {
        "total": len(memories),
        "by_type": {k: len(v) for k, v in by_type.items()},
        "avg_confidence": sum(m["confidence"] for m in memories) / len(memories),
        "high_confidence_count": high_confidence,
        "memory_quality": _assess_memory_quality(memories)
    }


def format_memory_for_display(memory: Dict) -> str:
    """
    Format a single memory for user display
    
    Args:
        memory: Memory dictionary
        
    Returns:
        str: Formatted memory string
    """
    mem_type = memory['type'].capitalize()
    content = memory['content']
    confidence = memory['confidence']
    
    confidence_emoji = _get_confidence_emoji(confidence)
    
    return f"{confidence_emoji} [{mem_type}] {content}"


def format_memories_for_display(memories: List[Dict]) -> List[str]:
    """
    Format multiple memories for user display
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        List of formatted strings
    """
    return [format_memory_for_display(m) for m in memories]


def create_memory_card(memory: Dict) -> Dict:
    """
    Create a rich memory card for UI display
    
    Args:
        memory: Memory dictionary
        
    Returns:
        Dict with formatted fields
    """
    return {
        "id": memory['id'],
        "type": memory['type'],
        "type_display": memory['type'].capitalize(),
        "content": memory['content'],
        "confidence": round(memory['confidence'], 2),
        "confidence_display": f"{round(memory['confidence'] * 100)}%",
        "confidence_level": _get_confidence_level(memory['confidence']),
        "relevance": round(memory.get('relevance', 0), 2) if 'relevance' in memory else None,
        "age": memory.get('created_turn', 0),
        "last_used": memory.get('last_used_turn', 0),
        "use_count": memory.get('use_count', 1)
    }


def _group_by_type(memories: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group memories by type
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        dict: Memories grouped by type
    """
    grouped = {}
    
    for mem in memories:
        mem_type = mem["type"]
        if mem_type not in grouped:
            grouped[mem_type] = []
        grouped[mem_type].append(mem)
    
    return grouped


def _get_type_title(mem_type: str) -> str:
    """Get display title for memory type"""
    titles = {
        "fact": "📋 Facts About User",
        "preference": "⭐ User Preferences",
        "constraint": "🚫 User Boundaries",
        "commitment": "📅 Pending Tasks",
        "goal": "🎯 User Goals",
        "relationship": "👥 Relationships"
    }
    return titles.get(mem_type, mem_type.capitalize())


def _get_confidence_indicator(confidence: float) -> str:
    """Get visual indicator for confidence level"""
    if confidence >= 0.95:
        return "●●●"  # Very high
    elif confidence >= 0.85:
        return "●●○"  # High
    elif confidence >= 0.75:
        return "●○○"  # Medium
    else:
        return "○○○"  # Low


def _get_confidence_emoji(confidence: float) -> str:
    """Get emoji for confidence level"""
    if confidence >= 0.9:
        return "🟢"  # High confidence
    elif confidence >= 0.8:
        return "🟡"  # Medium confidence
    else:
        return "🟠"  # Low confidence


def _get_confidence_level(confidence: float) -> str:
    """Get text description of confidence level"""
    if confidence >= 0.9:
        return "high"
    elif confidence >= 0.8:
        return "medium"
    elif confidence >= 0.7:
        return "moderate"
    else:
        return "low"


def _assess_memory_quality(memories: List[Dict]) -> str:
    """
    Assess overall quality of memory set
    
    Args:
        memories: List of memories
        
    Returns:
        str: Quality assessment
    """
    if not memories:
        return "none"
    
    avg_confidence = sum(m['confidence'] for m in memories) / len(memories)
    high_conf_ratio = len([m for m in memories if m['confidence'] > 0.9]) / len(memories)
    
    if avg_confidence > 0.9 and high_conf_ratio > 0.5:
        return "excellent"
    elif avg_confidence > 0.85:
        return "good"
    elif avg_confidence > 0.75:
        return "fair"
    else:
        return "poor"


def inject_with_relevance_scores(memories: List[Dict]) -> str:
    """
    Inject memories with relevance scores for debugging
    
    Args:
        memories: List of memories with relevance scores
        
    Returns:
        str: Formatted context with scores
    """
    if not memories:
        return ""
    
    lines = ["[Memory Context with Relevance]"]
    
    for mem in memories:
        relevance = mem.get('relevance', 0)
        confidence = mem['confidence']
        content = mem['content']
        
        lines.append(f"  [R:{relevance:.2f} C:{confidence:.2f}] {content}")
    
    lines.append("")
    
    return "\n".join(lines)
