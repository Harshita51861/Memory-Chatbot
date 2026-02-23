# backend/long_term/extractor.py

"""
Memory Extractor - Enhanced extraction with better pattern matching
Uses advanced NLP patterns and context awareness
"""

import uuid
import re
from typing import Dict, Optional, List
from .contract import MIN_CONFIDENCE, is_valid_memory, ALLOWED_TYPES


class MemoryExtractor:
    """Enhanced memory extraction with pattern matching and context"""
    
    def __init__(self):
        self.patterns = self._init_patterns()
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'}
    
    def _init_patterns(self) -> Dict:
        """Initialize extraction patterns"""
        return {
            "preference": {
                "patterns": [
                    r"i (prefer|like|love|enjoy|want|favor|choose)\s+(.+)",
                    r"i'd (prefer|like|love|rather)\s+(.+)",
                    r"my favorite\s+(.+)",
                    r"i (always|usually|often)\s+(.+)",
                    r"i'm (into|fond of)\s+(.+)"
                ],
                "keywords": ["prefer", "like", "love", "enjoy", "favorite", "want", "hate", "dislike"],
                "confidence": 0.88
            },
            "fact": {
                "patterns": [
                    r"my name is\s+(\w+)",
                    r"i am\s+(?:a|an)?\s*(\w+)",
                    r"i work (?:at|for)\s+(.+)",
                    r"i live in\s+(.+)",
                    r"i(?:'m| am)\s+(\d+)\s+years old",
                    r"i(?:'m| am) from\s+(.+)",
                    r"my\s+(\w+)\s+is\s+(.+)",
                    r"i have\s+(?:a|an)?\s*(.+)"
                ],
                "keywords": ["my name", "i am", "i work", "i live", "i have", "i'm from"],
                "confidence": 0.95
            },
            "constraint": {
                "patterns": [
                    r"(?:don't|do not|never)\s+(.+)",
                    r"i (?:can't|cannot|won't)\s+(.+)",
                    r"(?:not allowed|forbidden|prohibited)\s+(.+)",
                    r"(?:must not|shouldn't)\s+(.+)",
                    r"i (?:refuse|decline) to\s+(.+)"
                ],
                "keywords": ["don't", "never", "can't", "not allowed", "forbidden", "must not"],
                "confidence": 0.92
            },
            "commitment": {
                "patterns": [
                    r"remind me (?:to|about)\s+(.+)",
                    r"i (?:need|have) to\s+(.+)",
                    r"(?:schedule|book|plan)\s+(?:a|an)?\s*(.+)",
                    r"(?:meeting|call|appointment)\s+(?:with|at|on)\s+(.+)",
                    r"i'll\s+(.+)",
                    r"i (?:will|should)\s+(.+)"
                ],
                "keywords": ["remind", "schedule", "meeting", "appointment", "task", "todo", "deadline"],
                "confidence": 0.85
            },
            "goal": {
                "patterns": [
                    r"i want to\s+(.+)",
                    r"my goal is (?:to)?\s*(.+)",
                    r"i(?:'m| am) trying to\s+(.+)",
                    r"i hope to\s+(.+)",
                    r"i aim to\s+(.+)",
                    r"i plan to\s+(.+)"
                ],
                "keywords": ["goal", "aim", "objective", "plan to", "want to", "hope to"],
                "confidence": 0.87
            },
            "relationship": {
                "patterns": [
                    r"my\s+(wife|husband|partner|friend|colleague|boss|manager)\s+(?:is|named)\s+(\w+)",
                    r"(\w+)\s+is my\s+(wife|husband|partner|friend|colleague)",
                    r"i work with\s+(\w+)",
                    r"my\s+(son|daughter|child|parent)\s+(.+)"
                ],
                "keywords": ["my wife", "my husband", "my friend", "my colleague", "my boss", "my partner"],
                "confidence": 0.90
            }
        }
    
    def extract_memory(self, message: str, turn: int, user_id: str = "default") -> Optional[Dict]:
        """
        Enhanced memory extraction with pattern matching
        
        Args:
            message: User's message text
            turn: Current conversation turn number
            user_id: User identifier
            
        Returns:
            dict or None: Memory object if extracted, None otherwise
        """
        msg_lower = message.lower().strip()
        
        # Skip very short messages
        if len(msg_lower) < 3:
            return None
        
        # Try each memory type
        for mem_type, config in self.patterns.items():
            # Check keywords first for efficiency
            if any(keyword in msg_lower for keyword in config["keywords"]):
                # Try regex patterns
                for pattern in config["patterns"]:
                    match = re.search(pattern, msg_lower, re.IGNORECASE)
                    if match:
                        content = self._clean_content(message)
                        return self._create_memory(
                            mem_type, 
                            content, 
                            config["confidence"], 
                            turn, 
                            user_id
                        )
        
        # Check for time-based preferences
        if self._is_time_preference(msg_lower):
            return self._create_memory("preference", message, 0.88, turn, user_id)
        
        # Check for negative constraints
        if self._is_negative_statement(msg_lower):
            return self._create_memory("constraint", message, 0.85, turn, user_id)
        
        return None
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Capitalize first letter
        if content:
            content = content[0].upper() + content[1:]
        
        # Ensure ends with period if it's a statement
        if content and not content[-1] in '.!?':
            content += '.'
        
        return content
    
    def _is_time_preference(self, message: str) -> bool:
        """Check if message contains time-based preference"""
        time_words = ['morning', 'afternoon', 'evening', 'night', 'am', 'pm',
                     'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                     'saturday', 'sunday', 'weekday', 'weekend']
        
        temporal_words = ['after', 'before', 'between', 'during', 'at', 'on']
        
        has_time = any(word in message for word in time_words)
        has_temporal = any(word in message for word in temporal_words)
        
        return has_time and has_temporal
    
    def _is_negative_statement(self, message: str) -> bool:
        """Check if message contains negative constraint"""
        negative_words = ["don't", "do not", "never", "not", "won't", "will not",
                         "can't", "cannot", "shouldn't", "should not"]
        
        return any(word in message for word in negative_words)
    
    def _create_memory(self, mem_type: str, content: str, confidence: float, 
                      turn: int, user_id: str) -> Optional[Dict]:
        """
        Creates a validated memory dictionary
        
        Args:
            mem_type: Type of memory
            content: Memory content
            confidence: Confidence score (0-1)
            turn: Current turn number
            user_id: User identifier
            
        Returns:
            dict or None: Memory object if valid, None otherwise
        """
        memory = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": mem_type,
            "content": content,
            "confidence": confidence,
            "created_turn": turn,
            "last_used_turn": turn,
            "active": 1
        }
        
        # Validate before returning
        is_valid, error = is_valid_memory(memory)
        if is_valid:
            return memory
        
        print(f"Invalid memory: {error}")
        return None
    
    def extract_name(self, message: str) -> Optional[str]:
        """
        Enhanced name extraction
        
        Args:
            message: User message
            
        Returns:
            str or None: Extracted name or None
        """
        msg_lower = message.lower()
        
        # Pattern: "my name is X"
        match = re.search(r"my name is\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", msg_lower)
        if match:
            name = match.group(1)
            return self._capitalize_name(name)
        
        # Pattern: "i am X" (careful with false positives)
        match = re.search(r"i(?:'m| am)\s+([a-zA-Z]+)(?:\s|$|\.)", msg_lower)
        if match:
            name = match.group(1)
            # Avoid common false positives
            skip_words = {"a", "an", "the", "going", "working", "living", "from", "here"}
            if name not in skip_words:
                return self._capitalize_name(name)
        
        # Pattern: "call me X"
        match = re.search(r"call me\s+([a-zA-Z]+)", msg_lower)
        if match:
            return self._capitalize_name(match.group(1))
        
        return None
    
    def _capitalize_name(self, name: str) -> str:
        """Properly capitalize a name"""
        return ' '.join(word.capitalize() for word in name.split())
    
    def extract_multiple(self, message: str, turn: int, user_id: str = "default") -> List[Dict]:
        """
        Extract multiple memories from a single message
        
        Args:
            message: User message
            turn: Current turn
            user_id: User ID
            
        Returns:
            List of extracted memories
        """
        memories = []
        
        # Split by sentences
        sentences = re.split(r'[.!?]+', message)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 3:
                memory = self.extract_memory(sentence, turn, user_id)
                if memory:
                    memories.append(memory)
        
        return memories


# Standalone functions for backward compatibility
_extractor = MemoryExtractor()

def extract_memory(message: str, turn: int, user_id: str = "default") -> Optional[Dict]:
    """Extract memory from message"""
    return _extractor.extract_memory(message, turn, user_id)

def extract_name(message: str) -> Optional[str]:
    """Extract name from message"""
    return _extractor.extract_name(message)

def extract_multiple(message: str, turn: int, user_id: str = "default") -> List[Dict]:
    """Extract multiple memories from message"""
    return _extractor.extract_multiple(message, turn, user_id)
