#!/usr/bin/env python3

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from langchain_openai import ChatOpenAI
from tools.token_estimator import estimate_costs

class ConversationState(Enum):
    INITIAL_INQUIRY = "initial_inquiry"
    CLARIFYING_QUESTIONS = "clarifying_questions"
    SCOPE_REFINEMENT = "scope_refinement"
    PROPOSAL_REVIEW = "proposal_review"
    READY_TO_EXECUTE = "ready_to_execute"

@dataclass
class ProjectScope:
    business_question: str = ""
    industry: str = ""
    timeline: str = ""
    deliverables: List[str] = None
    budget_range: str = ""
    stakeholders: str = ""
    success_metrics: str = ""
    constraints: str = ""
    
    def __post_init__(self):
        if self.deliverables is None:
            self.deliverables = []

@dataclass
class ConversationContext:
    state: ConversationState
    scope: ProjectScope
    questions_asked: List[str]
    user_responses: List[str]
    clarifications_needed: List[str]
    
    def __post_init__(self):
        if self.questions_asked is None:
            self.questions_asked = []
        if self.user_responses is None:
            self.user_responses = []
        if self.clarifications_needed is None:
            self.clarifications_needed = []

class InteractiveManager:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.conversations: Dict[str, ConversationContext] = {}
    
    def start_conversation(self, user_id: str, initial_request: str) -> str:
        """Start a new conversation with initial scoping questions"""
        
        # Initialize conversation context
        scope = ProjectScope()
        context = ConversationContext(
            state=ConversationState.INITIAL_INQUIRY,
            scope=scope,
            questions_asked=[],
            user_responses=[initial_request],
            clarifications_needed=[]
        )
        
        self.conversations[user_id] = context
        
        # Generate initial scoping questions
        prompt = f"""
        You are an experienced engagement manager at a top-tier consulting firm. A client has approached you with this request:
        
        "{initial_request}"
        
        Your job is to understand their real business needs through strategic questioning. Generate 3-4 sharp, executive-level questions that will help you:
        1. Understand the core business problem
        2. Identify the decision they need to make
        3. Clarify the scope and timeline
        4. Understand success metrics
        
        Format your response as a friendly but professional message that includes:
        - A brief acknowledgment of their request
        - 3-4 strategic questions
        - An explanation of why you're asking these questions
        
        Keep it conversational and executive-appropriate.
        """
        
        response = self.llm.invoke(prompt)
        context.state = ConversationState.CLARIFYING_QUESTIONS
        
        return response.content
    
    def continue_conversation(self, user_id: str, user_response: str) -> str:
        """Continue the conversation based on current state"""
        
        if user_id not in self.conversations:
            return "I don't have context for our conversation. Please start with your business question or request."
        
        context = self.conversations[user_id]
        context.user_responses.append(user_response)
        
        if context.state == ConversationState.CLARIFYING_QUESTIONS:
            return self._handle_clarifying_response(context, user_response)
        elif context.state == ConversationState.SCOPE_REFINEMENT:
            return self._handle_scope_refinement(context, user_response)
        elif context.state == ConversationState.PROPOSAL_REVIEW:
            return self._handle_proposal_feedback(context, user_response)
        else:
            return self._generate_contextual_response(context, user_response)
    
    def _handle_clarifying_response(self, context: ConversationContext, response: str) -> str:
        """Process responses to clarifying questions"""
        
        # Acknowledge the user's response
        acknowledgment = f"Thank you for your detailed response. I've noted:\n"
        acknowledgment += f"- {response}\n\n"
        
        # Extract information from response to update scope
        extraction_prompt = f"""
        Based on this client response, extract key project information:
        
        Response: "{response}"
        
        Extract and structure the following if mentioned:
        - Business question/problem
        - Industry/sector
        - Timeline/urgency
        - Key stakeholders
        - Success metrics
        - Budget considerations
        - Constraints
        
        Format as JSON with keys: business_question, industry, timeline, stakeholders, success_metrics, budget_range, constraints
        If information isn't provided, use empty string.
        """
        
        extraction_result = self.llm.invoke(extraction_prompt)
        
        # Update scope (in a real implementation, you'd parse the JSON)
        # For now, we'll continue with the conversation flow
        
        # Determine if we need more clarification or can move to proposal
        assessment_prompt = f"""
        Based on the client's response: "{response}"
        
        And the conversation history: {context.user_responses}
        
        Do we have enough information to create a project proposal, or do we need more clarification?
        
        If we need more clarification, generate 1-2 follow-up questions.
        If we have enough information, indicate we're ready to create a proposal.
        
        Respond with either:
        "CLARIFY: [questions]" or "PROPOSAL_READY"
        """
        
        assessment = self.llm.invoke(assessment_prompt)
        
        if "PROPOSAL_READY" in assessment.content:
            context.state = ConversationState.PROPOSAL_REVIEW
            return self._generate_proposal(context)
        else:
            # Extract questions and continue clarifying
            questions = assessment.content.replace("CLARIFY:", "").strip()
            return f"{acknowledgment}To ensure we scope this correctly, I have a couple more questions:\n\n{questions}\n\nAfter reviewing, please type 'approve' to confirm the final scope."
    
    def _generate_proposal(self, context: ConversationContext) -> str:
        """Generate a project proposal based on gathered information"""
        
        proposal_prompt = f"""
        Based on our conversation: {context.user_responses}
        
        Create a concise project proposal that includes:
        1. Project objective (what we'll help them achieve)
        2. Key deliverables (3-4 specific outputs)
        3. Proposed approach (high-level methodology)
        4. Estimated timeline
        5. Team composition (which specialists we'll deploy)
        6. Next steps for approval
        
        Format this as a professional but conversational proposal.
        End with: "Does this approach align with your needs? Please review and type 'approve' to confirm or suggest any adjustments."
        """
        
        proposal = self.llm.invoke(proposal_prompt)
        return proposal.content
    
    def _handle_scope_refinement(self, context: ConversationContext, response: str) -> str:
        """Handle requests for scope changes"""
        
        refinement_prompt = f"""
        The client has provided feedback on our proposal: "{response}"
        
        Generate a response that:
        1. Acknowledges their feedback
        2. Clarifies any requested changes
        3. Asks for confirmation on the refined scope
        
        Keep it collaborative and solution-oriented.
        """
        
        refinement = self.llm.invoke(refinement_prompt)
        return refinement.content
    
    def _handle_proposal_feedback(self, context: ConversationContext, response: str) -> str:
        """Handle feedback on the proposal"""
        
        if any(word in response.lower() for word in ["approve", "yes", "proceed", "looks good", "agree"]):
            context.state = ConversationState.READY_TO_EXECUTE
            return self._generate_execution_plan(context)
        else:
            context.state = ConversationState.SCOPE_REFINEMENT
            return self._handle_scope_refinement(context, response)
    
    def _generate_execution_plan(self, context: ConversationContext) -> str:
        """Generate the final execution plan"""
        
        execution_prompt = f"""
        The client has approved our proposal. Based on our conversation: {context.user_responses}
        
        Generate a final execution message that:
        1. Confirms the approved scope
        2. Outlines the team deployment plan
        3. Sets expectations for deliverables and timeline
        4. Provides next steps
        
        End with a clear call to action for them to confirm final approval.
        """
        
        execution_plan = self.llm.invoke(execution_prompt)
        return execution_plan.content
    
    def _generate_contextual_response(self, context: ConversationContext, response: str) -> str:
        """Generate a contextual response for any state"""
        
        contextual_prompt = f"""
        Continue this consulting conversation naturally. 
        
        Conversation history: {context.user_responses}
        Current state: {context.state.value}
        Latest response: "{response}"
        
        Provide a helpful, professional response that moves the conversation forward toward defining a clear project scope.
        """
        
        contextual_response = self.llm.invoke(contextual_prompt)
        return contextual_response.content
    
    def is_ready_to_execute(self, user_id: str) -> bool:
        """Check if the conversation is ready for team deployment"""
        if user_id not in self.conversations:
            return False
        return self.conversations[user_id].state == ConversationState.READY_TO_EXECUTE
    
    def get_final_scope(self, user_id: str) -> Optional[str]:
        """Get the final project scope for team deployment"""
        if user_id not in self.conversations:
            return None
        
        context = self.conversations[user_id]
        
        scope_prompt = f"""
        Based on this conversation: {context.user_responses}
        
        Generate a clear, concise project brief that can be used to deploy the analyst team:
        
        Format:
        **Project Brief**
        - Objective: [what we're solving]
        - Key Questions: [specific questions to answer]
        - Deliverables: [what we'll produce]
        - Timeline: [when it's needed]
        - Success Criteria: [how we'll measure success]
        """
        
        brief = self.llm.invoke(scope_prompt)
        return brief.content
    
    def reset_conversation(self, user_id: str):
        """Reset conversation for a user"""
        if user_id in self.conversations:
            del self.conversations[user_id]

# Example usage and testing
if __name__ == "__main__":
    manager = InteractiveManager()
    
    # Test conversation flow
    user_id = "test_user"
    initial_request = "I need to understand the market opportunity for electric vehicle charging stations"
    
    response1 = manager.start_conversation(user_id, initial_request)
    print("Manager:", response1)
    
    user_response = "We're looking at commercial real estate opportunities and want to understand if EV charging could be a profitable amenity. We need this analysis in the next 3 weeks for a board presentation."
    
    response2 = manager.continue_conversation(user_id, user_response)
    print("\nManager:", response2)