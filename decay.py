# backend/long_term/decay.py

"""
Memory Decay - Enhanced human-like forgetting mechanism
Implements smart decay based on memory type, usage, and importance
"""

from typing import List, Tuple
from .contract import (
    DECAY_RATE, MIN_CONFIDENCE, DECAY_MULTIPLIER, 
    MIN_MEMORY_AGE_FOR_DECAY, calculate_decay_amount
)


def apply_decay(store, user_id: str, current_turn: int):
    """
    Apply intelligent time-based decay to all active memories
    Memories that fall below MIN_CONFIDENCE are deactivated
    
    Args:
        store: MemoryStore instance
        user_id: User identifier
        current_turn: Current conversation turn
    """
    memories = store.fetch_active(user_id)
    
    for mem in memories:
        mem_id = mem[0]
        mem_type = mem[1]
        confidence = mem[3]
        created_turn = mem[4]
        last_used = mem[5]
        use_count = mem[6] if len(mem) > 6 else 1
        
        # Calculate age since last use
        age = current_turn - last_used
        
        # Skip recently created or used memories
        if age < MIN_MEMORY_AGE_FOR_DECAY:
            continue
        
        # Calculate decay amount based on type and age
        decay_amount = calculate_decay_amount(mem_type, age, confidence)
        
        # Apply usage-based retention bonus
        # Frequently used memories decay slower
        if use_count > 1:
            usage_bonus = min(0.1, use_count * 0.01)
            decay_amount *= (1 - usage_bonus)
        
        # Calculate new confidence
        new_confidence = max(0, confidence - decay_amount)
        
        # Deactivate if below threshold
        if new_confidence < MIN_CONFIDENCE:
            store.deactivate(mem_id)
            print(f"Memory {mem_id[:8]} deactivated (confidence: {new_confidence:.2f})")
        else:
            # Update confidence
            store.update_confidence(mem_id, new_confidence)


def apply_selective_decay(store, user_id: str, current_turn: int, 
                         memory_types: List[str] = None):
    """
    Apply decay only to specific memory types
    
    Args:
        store: MemoryStore instance
        user_id: User identifier
        current_turn: Current turn
        memory_types: List of memory types to decay (None = all)
    """
    memories = store.fetch_active(user_id)
    
    for mem in memories:
        mem_id = mem[0]
        mem_type = mem[1]
        
        # Skip if not in target types
        if memory_types and mem_type not in memory_types:
            continue
        
        confidence = mem[3]
        last_used = mem[5]
        
        age = current_turn - last_used
        
        if age < MIN_MEMORY_AGE_FOR_DECAY:
            continue
        
        decay_amount = calculate_decay_amount(mem_type, age, confidence)
        new_confidence = max(0, confidence - decay_amount)
        
        if new_confidence < MIN_CONFIDENCE:
            store.deactivate(mem_id)
        else:
            store.update_confidence(mem_id, new_confidence)


def refresh_memory(store, mem_id: str, current_turn: int, boost: float = 0.0):
    """
    Refresh a memory when it's used (reset its decay)
    Optionally boost confidence
    
    Args:
        store: MemoryStore instance
        mem_id: Memory ID
        current_turn: Current turn
        boost: Optional confidence boost (0-0.1)
    """
    store.update_last_used(mem_id, current_turn)
    
    # Optional confidence boost for reinforcement
    if boost > 0:
        memories = store.fetch_active(store.user_id)
        for mem in memories:
            if mem[0] == mem_id:
                old_confidence = mem[3]
                new_confidence = min(0.99, old_confidence + boost)
                store.update_confidence(mem_id, new_confidence)
                break


def boost_related_memories(store, user_id: str, current_turn: int, 
                          keywords: List[str], boost_amount: float = 0.02):
    """
    Boost confidence of memories related to current conversation
    
    Args:
        store: MemoryStore instance
        user_id: User ID
        current_turn: Current turn
        keywords: Keywords to search for
        boost_amount: Amount to boost confidence
    """
    memories = store.fetch_active(user_id)
    
    for mem in memories:
        mem_id = mem[0]
        content = mem[2].lower()
        confidence = mem[3]
        
        # Check if any keyword is in content
        if any(keyword.lower() in content for keyword in keywords):
            new_confidence = min(0.99, confidence + boost_amount)
            store.update_confidence(mem_id, new_confidence)
            refresh_memory(store, mem_id, current_turn)


def consolidate_memories(store, user_id: str, current_turn: int):
    """
    Consolidate similar memories to prevent redundancy
    Merges memories with similar content
    
    Args:
        store: MemoryStore instance
        user_id: User ID
        current_turn: Current turn
    """
    from .contract import should_merge_memories
    
    memories = store.fetch_active(user_id)
    processed = set()
    
    for i, mem1 in enumerate(memories):
        mem1_id = mem1[0]
        
        if mem1_id in processed:
            continue
        
        mem1_dict = {
            'type': mem1[1],
            'content': mem1[2],
            'confidence': mem1[3]
        }
        
        for j in range(i + 1, len(memories)):
            mem2 = memories[j]
            mem2_id = mem2[0]
            
            if mem2_id in processed:
                continue
            
            mem2_dict = {
                'type': mem2[1],
                'content': mem2[2],
                'confidence': mem2[3]
            }
            
            # Check if should merge
            if should_merge_memories(mem1_dict, mem2_dict):
                # Keep the one with higher confidence
                if mem1_dict['confidence'] >= mem2_dict['confidence']:
                    # Boost mem1, deactivate mem2
                    new_confidence = min(0.99, mem1_dict['confidence'] + 0.05)
                    store.update_confidence(mem1_id, new_confidence)
                    store.deactivate(mem2_id)
                    processed.add(mem2_id)
                else:
                    # Boost mem2, deactivate mem1
                    new_confidence = min(0.99, mem2_dict['confidence'] + 0.05)
                    store.update_confidence(mem2_id, new_confidence)
                    store.deactivate(mem1_id)
                    processed.add(mem1_id)
                    break


def prune_low_priority_memories(store, user_id: str, max_memories: int = 100):
    """
    Remove lowest priority memories when count exceeds limit
    
    Args:
        store: MemoryStore instance
        user_id: User ID
        max_memories: Maximum number of active memories
    """
    from .contract import get_memory_priority
    
    memories = store.fetch_active(user_id)
    
    if len(memories) <= max_memories:
        return
    
    # Calculate priority for each memory
    scored_memories = []
    for mem in memories:
        mem_id = mem[0]
        mem_type = mem[1]
        confidence = mem[3]
        created_turn = mem[4]
        last_used = mem[5]
        
        age = last_used - created_turn
        priority = get_memory_priority(mem_type, confidence, age)
        
        scored_memories.append((mem_id, priority))
    
    # Sort by priority (lowest first)
    scored_memories.sort(key=lambda x: x[1])
    
    # Deactivate lowest priority memories
    to_remove = len(memories) - max_memories
    for i in range(to_remove):
        mem_id = scored_memories[i][0]
        store.deactivate(mem_id)
        print(f"Pruned low-priority memory: {mem_id[:8]}")


def apply_smart_decay(store, user_id: str, current_turn: int):
    """
    Enhanced decay that considers multiple factors
    
    Args:
        store: MemoryStore instance
        user_id: User ID
        current_turn: Current turn
    """
    # 1. Apply standard decay
    apply_decay(store, user_id, current_turn)
    
    # 2. Consolidate similar memories
    if current_turn % 10 == 0:  # Every 10 turns
        consolidate_memories(store, user_id, current_turn)
    
    # 3. Prune if too many memories
    if current_turn % 20 == 0:  # Every 20 turns
        prune_low_priority_memories(store, user_id)


def get_decay_stats(store, user_id: str, current_turn: int) -> dict:
    """
    Get statistics about memory decay
    
    Args:
        store: MemoryStore instance
        user_id: User ID
        current_turn: Current turn
        
    Returns:
        Dictionary with decay statistics
    """
    memories = store.fetch_active(user_id)
    
    total = len(memories)
    at_risk = 0  # Close to MIN_CONFIDENCE
    stable = 0   # High confidence
    
    for mem in memories:
        confidence = mem[3]
        
        if confidence < MIN_CONFIDENCE + 0.1:
            at_risk += 1
        elif confidence > 0.85:
            stable += 1
    
    return {
        "total_active": total,
        "stable_memories": stable,
        "at_risk_memories": at_risk,
        "healthy_percentage": round((stable / total * 100) if total > 0 else 0, 1)
    }
