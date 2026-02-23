# backend/long_term/contract.py

"""
Memory Contract - Enhanced validation and configuration
Defines what is allowed to become memory with stricter rules
"""

from typing import Dict, Any
from datetime import datetime

# Allowed memory types with descriptions
ALLOWED_TYPES = {
    "preference": "User likes, dislikes, and preferences",
    "fact": "Factual information about the user",
    "constraint": "Boundaries and restrictions",
    "commitment": "Tasks, reminders, and future obligations",
    "goal": "Long-term objectives and aspirations",
    "relationship": "Information about other people"
}

# Confidence thresholds
MIN_CONFIDENCE = 0.7
HIGH_CONFIDENCE = 0.9

# Decay configuration
DECAY_RATE = 0.008  # Slower decay for better retention
DECAY_MULTIPLIER = {
    "fact": 0.5,        # Facts decay slower
    "preference": 1.0,  # Normal decay
    "constraint": 0.3,  # Constraints persist longer
    "commitment": 1.5,  # Commitments decay faster (time-sensitive)
    "goal": 0.4,        # Goals persist
    "relationship": 0.6 # Relationships persist
}

# Memory limits
MAX_MEMORIES_PER_TYPE = 100
MAX_TOTAL_MEMORIES = 500
MIN_MEMORY_AGE_FOR_DECAY = 2  # Don't decay memories newer than 2 turns

# Content validation
MIN_CONTENT_LENGTH = 3
MAX_CONTENT_LENGTH = 500


def is_valid_memory(memory_dict: Dict[str, Any]) -> tuple[bool, str]:
    """
    Enhanced validation with detailed error messages
    
    Args:
        memory_dict: Dictionary containing memory fields
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    required_fields = {"id", "type", "content", "confidence", "created_turn", "active"}
    
    # Check all required fields exist
    missing_fields = required_fields - set(memory_dict.keys())
    if missing_fields:
        return False, f"Missing required fields: {missing_fields}"
    
    # Check type is allowed
    if memory_dict["type"] not in ALLOWED_TYPES:
        return False, f"Invalid type '{memory_dict['type']}'. Allowed: {list(ALLOWED_TYPES.keys())}"
    
    # Check confidence is valid
    confidence = memory_dict["confidence"]
    if not isinstance(confidence, (int, float)):
        return False, "Confidence must be a number"
    
    if not (0 <= confidence <= 1):
        return False, f"Confidence must be between 0 and 1, got {confidence}"
    
    # Check meets minimum confidence
    if confidence < MIN_CONFIDENCE:
        return False, f"Confidence {confidence} below minimum {MIN_CONFIDENCE}"
    
    # Check content validity
    content = memory_dict.get("content", "")
    if not isinstance(content, str):
        return False, "Content must be a string"
    
    content = content.strip()
    if len(content) < MIN_CONTENT_LENGTH:
        return False, f"Content too short (minimum {MIN_CONTENT_LENGTH} characters)"
    
    if len(content) > MAX_CONTENT_LENGTH:
        return False, f"Content too long (maximum {MAX_CONTENT_LENGTH} characters)"
    
    # Check turn numbers
    created_turn = memory_dict.get("created_turn")
    if not isinstance(created_turn, int) or created_turn < 0:
        return False, "Invalid created_turn value"
    
    # Check active flag
    active = memory_dict.get("active")
    if active not in [0, 1, True, False]:
        return False, "Active must be boolean or 0/1"
    
    return True, "Valid"


def calculate_decay_amount(memory_type: str, age: int, base_confidence: float) -> float:
    """
    Calculate decay amount based on memory type and age
    
    Args:
        memory_type: Type of memory
        age: Age in turns
        base_confidence: Original confidence
        
    Returns:
        float: Decay amount to subtract
    """
    if age < MIN_MEMORY_AGE_FOR_DECAY:
        return 0.0
    
    multiplier = DECAY_MULTIPLIER.get(memory_type, 1.0)
    decay = DECAY_RATE * multiplier * age
    
    # Exponential decay for very old memories
    if age > 50:
        decay *= 1.5
    if age > 100:
        decay *= 2.0
    
    return min(decay, base_confidence - MIN_CONFIDENCE + 0.01)


def should_merge_memories(mem1: Dict, mem2: Dict) -> bool:
    """
    Determine if two memories should be merged
    
    Args:
        mem1: First memory
        mem2: Second memory
        
    Returns:
        bool: True if memories should be merged
    """
    # Same type
    if mem1["type"] != mem2["type"]:
        return False
    
    # Similar content (simple check - can be improved with embeddings)
    content1_words = set(mem1["content"].lower().split())
    content2_words = set(mem2["content"].lower().split())
    
    if len(content1_words) == 0 or len(content2_words) == 0:
        return False
    
    overlap = len(content1_words & content2_words)
    total = len(content1_words | content2_words)
    
    similarity = overlap / total if total > 0 else 0
    
    return similarity > 0.7


def get_memory_priority(memory_type: str, confidence: float, age: int) -> float:
    """
    Calculate priority score for memory
    Higher score = more important to keep
    
    Args:
        memory_type: Type of memory
        confidence: Confidence score
        age: Age in turns
        
    Returns:
        float: Priority score
    """
    type_weights = {
        "fact": 1.2,
        "preference": 1.0,
        "constraint": 1.3,
        "commitment": 0.8,  # Lower priority as they're time-sensitive
        "goal": 1.1,
        "relationship": 1.0
    }
    
    type_weight = type_weights.get(memory_type, 1.0)
    recency_score = max(0, 1 - (age * 0.01))  # Decreases with age
    
    return confidence * type_weight * (0.3 + 0.7 * recency_score)
