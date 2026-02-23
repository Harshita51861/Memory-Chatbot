# backend/llm/simple_llm.py

"""
Enhanced LLM - Improved rule-based response generation
Better pattern matching and context-aware responses
Can be easily replaced with real LLM API
"""

import random
import re
from typing import Dict, List, Optional


class SimpleLLM:
    """Enhanced rule-based chatbot with better context awareness"""
    
    def __init__(self):
        self.patterns = self._init_patterns()
        self.context_handlers = self._init_context_handlers()
    
    def _init_patterns(self) -> Dict[str, List[str]]:
        """Initialize response patterns"""
        return {
            "greeting": [
                "Hello{name}! How can I help you today?",
                "Hi{name}! What can I do for you?",
                "Hey{name}! Nice to {meet_again}!",
                "Hello{name}! I'm here to assist you."
            ],
            "greeting_with_memory": [
                "Hello{name}! Good to see you again. How can I help?",
                "Hi{name}! I remember our last conversation. What's on your mind?",
                "Hey{name}! What would you like to talk about today?"
            ],
            "name_introduction": [
                "Nice to meet you, {name}! I'll remember that.",
                "Great to meet you, {name}! I've noted your name.",
                "Hello {name}! Pleasure to make your acquaintance.",
                "Pleased to meet you, {name}! I'll keep that in mind."
            ],
            "preference_noted": [
                "Got it! I've noted your preference for {subject}.",
                "Understood! I'll remember that you {preference}.",
                "Perfect! I've added that to what I know about your preferences.",
                "Noted! I'll keep that preference in mind going forward."
            ],
            "constraint_noted": [
                "I understand and will respect that boundary.",
                "Got it! I'll make sure to honor that constraint.",
                "Understood! I'll remember that restriction.",
                "I'll respect that - duly noted!"
            ],
            "commitment_noted": [
                "I've added that to your task list.",
                "Noted! I'll help you remember about {task}.",
                "Got it! I've recorded that commitment.",
                "Added to your to-do items!"
            ],
            "goal_noted": [
                "Great goal! I'll help you work towards {goal}.",
                "I've noted your objective. Let's work on achieving it!",
                "Excellent! I'll keep your goal in mind.",
                "That's a worthy goal! I'll remember it."
            ],
            "memory_recall": [
                "Based on what I know about you, {context}",
                "I recall that {context}",
                "From our previous conversations, I remember {context}",
                "According to what you've told me, {context}"
            ],
            "no_memory_yet": [
                "I don't have that information yet. Could you tell me more?",
                "I haven't learned about that. Can you share more details?",
                "I don't know that yet. What can you tell me?",
                "I'd like to learn more about that. Could you elaborate?"
            ],
            "question_with_context": [
                "Based on your preference for {pref}, I'd suggest {suggestion}.",
                "Given that {context}, I think {answer}.",
                "Considering what I know about you, {response}."
            ],
            "goodbye": [
                "Goodbye{name}! Have a great day!",
                "See you later{name}! Take care!",
                "Farewell{name}! Until next time!",
                "Bye{name}! Looking forward to our next chat!"
            ],
            "default": [
                "I understand. Is there anything else you'd like to talk about?",
                "Got it! What else can I help you with?",
                "I see. How else can I assist you?",
                "Understood! Anything else on your mind?"
            ],
            "default_with_name": [
                "I understand, {name}. What else would you like to discuss?",
                "Got it, {name}! How else can I help?",
                "I see, {name}. Is there anything else?",
                "Understood, {name}! What's next?"
            ]
        }
    
    def _init_context_handlers(self) -> Dict:
        """Initialize context-aware response handlers"""
        return {
            "name_query": self._handle_name_query,
            "preference_query": self._handle_preference_query,
            "time_query": self._handle_time_query,
            "task_query": self._handle_task_query,
            "general_query": self._handle_general_query
        }
    
    def generate_response(self, message: str, memory_context: str = "", 
                         new_memory: Dict = None, user_name: str = "User") -> str:
        """
        Enhanced response generation with context awareness
        
        Args:
            message: User's message
            memory_context: Injected memory context
            new_memory: Newly created memory (if any)
            user_name: User's name from memory
            
        Returns:
            str: Generated response
        """
        msg_lower = message.lower().strip()
        has_name = user_name != "User"
        has_memory = bool(memory_context)
        
        # 1. Handle greetings
        if self._is_greeting(msg_lower):
            return self._handle_greeting(has_name, has_memory, user_name)
        
        # 2. Handle name introduction
        if "my name is" in msg_lower or self._is_name_intro(msg_lower):
            return self._handle_name_introduction(user_name)
        
        # 3. Handle new memory creation
        if new_memory:
            return self._handle_new_memory(new_memory, user_name)
        
        # 4. Handle questions with memory context
        if self._is_question(message):
            return self._handle_question(msg_lower, memory_context, user_name)
        
        # 5. Handle scheduling/time-based requests
        if self._is_scheduling(msg_lower):
            return self._handle_scheduling(msg_lower, memory_context, user_name)
        
        # 6. Handle goodbyes
        if self._is_goodbye(msg_lower):
            return self._handle_goodbye(user_name)
        
        # 7. Handle statements/comments
        if has_memory or has_name:
            return self._format_response("default_with_name", name=user_name)
        
        # 8. Default response
        return random.choice(self.patterns["default"])
    
    def _is_greeting(self, msg: str) -> bool:
        """Check if message is a greeting"""
        greetings = ["hi", "hello", "hey", "greetings", "good morning", 
                    "good afternoon", "good evening", "howdy", "sup", "yo"]
        return any(msg.startswith(g) or msg == g for g in greetings)
    
    def _is_question(self, msg: str) -> bool:
        """Check if message is a question"""
        question_words = ["what", "when", "where", "who", "why", "how", "can you", 
                         "could you", "would you", "do you", "are you", "is there"]
        return "?" in msg or any(msg.lower().startswith(qw) for qw in question_words)
    
    def _is_scheduling(self, msg: str) -> bool:
        """Check if message is about scheduling"""
        scheduling_words = ["meeting", "schedule", "call", "appointment", 
                           "book", "plan", "calendar", "reminder"]
        return any(word in msg for word in scheduling_words)
    
    def _is_goodbye(self, msg: str) -> bool:
        """Check if message is a goodbye"""
        goodbyes = ["bye", "goodbye", "see you", "farewell", "later", "take care"]
        return any(gb in msg for gb in goodbyes)
    
    def _is_name_intro(self, msg: str) -> bool:
        """Check if message introduces a name"""
        patterns = ["i am ", "i'm ", "call me ", "this is "]
        return any(p in msg for p in patterns)
    
    def _handle_greeting(self, has_name: bool, has_memory: bool, user_name: str) -> str:
        """Handle greeting messages"""
        name_str = f" {user_name}" if has_name else ""
        meet_str = "see you again" if has_memory else "meet you"
        
        if has_memory and has_name:
            response = random.choice(self.patterns["greeting_with_memory"])
        else:
            response = random.choice(self.patterns["greeting"])
        
        return response.format(name=name_str, meet_again=meet_str)
    
    def _handle_name_introduction(self, user_name: str) -> str:
        """Handle name introduction"""
        return random.choice(self.patterns["name_introduction"]).format(name=user_name)
    
    def _handle_new_memory(self, new_memory: Dict, user_name: str) -> str:
        """Handle response when new memory is created"""
        mem_type = new_memory.get("type", "")
        content = new_memory.get("content", "")
        
        if mem_type == "preference":
            # Extract what they prefer
            subject = self._extract_preference_subject(content)
            preference = content
            return self._format_response(
                "preference_noted", 
                subject=subject if subject else "that",
                preference=preference
            )
        
        elif mem_type == "constraint":
            return random.choice(self.patterns["constraint_noted"])
        
        elif mem_type == "commitment":
            task = self._extract_task(content)
            return self._format_response("commitment_noted", task=task if task else "that")
        
        elif mem_type == "goal":
            goal = self._extract_goal(content)
            return self._format_response("goal_noted", goal=goal if goal else "that")
        
        elif mem_type == "fact":
            return f"Thanks for sharing! I've noted that information."
        
        return random.choice(self.patterns["default"])
    
    def _handle_question(self, msg: str, memory_context: str, user_name: str) -> str:
        """Handle questions using memory context"""
        # Name query
        if "my name" in msg or "what's my name" in msg or "who am i" in msg:
            return self._handle_name_query(user_name, memory_context)
        
        # Preference query
        if any(word in msg for word in ["prefer", "like", "favorite", "love"]):
            return self._handle_preference_query(memory_context)
        
        # Time/schedule query
        if any(word in msg for word in ["when", "time", "schedule"]):
            return self._handle_time_query(memory_context)
        
        # Task query
        if any(word in msg for word in ["task", "todo", "remind", "commitment"]):
            return self._handle_task_query(memory_context)
        
        # General query with context
        return self._handle_general_query(msg, memory_context, user_name)
    
    def _handle_name_query(self, user_name: str, memory_context: str) -> str:
        """Handle name queries"""
        if user_name != "User":
            return f"Your name is {user_name}!"
        else:
            return "I don't know your name yet. What should I call you?"
    
    def _handle_preference_query(self, memory_context: str) -> str:
        """Handle preference queries"""
        if not memory_context:
            return random.choice(self.patterns["no_memory_yet"])
        
        # Extract preferences from context
        prefs = self._extract_from_context(memory_context, "preference")
        if prefs:
            return f"Based on what you've told me, {prefs[0].lower()}"
        
        return "I don't have information about your preferences yet."
    
    def _handle_time_query(self, memory_context: str) -> str:
        """Handle time/schedule queries"""
        if not memory_context:
            return "I don't have any scheduling information yet. What would you like to know?"
        
        prefs = self._extract_from_context(memory_context, "preference")
        if prefs:
            return f"You mentioned that {prefs[0].lower()}. Does that help?"
        
        return "I don't have specific timing information. Can you tell me more?"
    
    def _handle_task_query(self, memory_context: str) -> str:
        """Handle task/commitment queries"""
        if not memory_context:
            return "You don't have any tasks or commitments recorded yet."
        
        tasks = self._extract_from_context(memory_context, "commitment")
        if tasks:
            return f"You have this on your list: {tasks[0]}"
        
        return "I don't see any pending tasks."
    
    def _handle_general_query(self, msg: str, memory_context: str, user_name: str) -> str:
        """Handle general queries"""
        if not memory_context:
            return random.choice(self.patterns["no_memory_yet"])
        
        # Try to extract relevant info from context
        context_info = self._extract_relevant_context(msg, memory_context)
        
        if context_info:
            response = random.choice(self.patterns["memory_recall"])
            return response.format(context=context_info)
        
        return random.choice(self.patterns["default"])
    
    def _handle_scheduling(self, msg: str, memory_context: str, user_name: str) -> str:
        """Handle scheduling requests"""
        if memory_context and "prefer" in memory_context.lower():
            return "Based on your preferences, I can help with that! When would work best for you?"
        
        return "Sure! When would you like to schedule that?"
    
    def _handle_goodbye(self, user_name: str) -> str:
        """Handle goodbye messages"""
        name_str = f" {user_name}" if user_name != "User" else ""
        response = random.choice(self.patterns["goodbye"])
        return response.format(name=name_str)
    
    def _extract_preference_subject(self, content: str) -> Optional[str]:
        """Extract what the preference is about"""
        # Simple extraction - look for common patterns
        patterns = [
            r"(?:prefer|like|love|enjoy)\s+(\w+)",
            r"favorite\s+(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                return match.group(1)
        
        return None
    
    def _extract_task(self, content: str) -> Optional[str]:
        """Extract task from commitment"""
        # Look for "remind me to X" or similar
        patterns = [
            r"remind me (?:to|about)\s+(.+)",
            r"(?:need|have) to\s+(.+)",
            r"(?:schedule|book)\s+(.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                return match.group(1)
        
        return content
    
    def _extract_goal(self, content: str) -> Optional[str]:
        """Extract goal from content"""
        patterns = [
            r"want to\s+(.+)",
            r"goal (?:is|:)\s+(.+)",
            r"(?:trying|planning|hoping) to\s+(.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                return match.group(1)
        
        return content
    
    def _extract_from_context(self, context: str, keyword: str) -> List[str]:
        """Extract items from context containing keyword"""
        lines = context.split('\n')
        results = []
        
        for line in lines:
            if keyword.lower() in line.lower() and '-' in line:
                # Extract content after dash
                parts = line.split('-', 1)
                if len(parts) > 1:
                    results.append(parts[1].strip())
        
        return results
    
    def _extract_relevant_context(self, msg: str, context: str) -> Optional[str]:
        """Extract most relevant context for the message"""
        msg_words = set(msg.lower().split())
        context_lines = context.split('\n')
        
        best_match = None
        best_score = 0
        
        for line in context_lines:
            if '-' not in line:
                continue
            
            line_words = set(line.lower().split())
            overlap = len(msg_words & line_words)
            
            if overlap > best_score:
                best_score = overlap
                parts = line.split('-', 1)
                if len(parts) > 1:
                    best_match = parts[1].strip()
        
        return best_match
    
    def _format_response(self, pattern_key: str, **kwargs) -> str:
        """Format a response with placeholders"""
        if pattern_key not in self.patterns:
            return random.choice(self.patterns["default"])
        
        response = random.choice(self.patterns[pattern_key])
        
        try:
            return response.format(**kwargs)
        except KeyError:
            return response
    
    def summarize_memory(self, memories: List[Dict]) -> str:
        """
        Create a natural summary of memories
        
        Args:
            memories: List of memory dictionaries
            
        Returns:
            str: Natural language summary
        """
        if not memories:
            return "I don't know much about you yet."
        
        summary_parts = []
        
        # Group by type
        by_type = {}
        for mem in memories:
            mem_type = mem.get("type", "unknown")
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(mem["content"])
        
        # Create summary
        if "fact" in by_type:
            summary_parts.append(f"I know that {by_type['fact'][0].lower()}")
        
        if "preference" in by_type:
            prefs = ", ".join(by_type['preference'][:2]).lower()
            summary_parts.append(f"you prefer {prefs}")
        
        if "constraint" in by_type:
            summary_parts.append(f"you've set some boundaries")
        
        if "commitment" in by_type:
            summary_parts.append(f"you have {len(by_type['commitment'])} pending task(s)")
        
        if len(summary_parts) == 1:
            return summary_parts[0]
        elif len(summary_parts) == 2:
            return f"{summary_parts[0]} and {summary_parts[1]}"
        else:
            return f"{', '.join(summary_parts[:-1])}, and {summary_parts[-1]}"
