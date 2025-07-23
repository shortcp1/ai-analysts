#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from crewai import Task, Crew, Process
from crew_config import create_agents
import requests
import json

# Load environment variables
load_dotenv()

class AnalystCrew:
    def __init__(self):
        self.manager, self.consultant, self.researcher, self.data_engineer, self.viz_analyst = create_agents()
    
    def create_tasks(self, user_request):
        # Create scoping task
        scoping_task = Task(
            description=f"""
            A client has requested: "{user_request}"
            
            Your job as Engagement Manager:
            1. Ask 3-5 sharp clarifying questions about what they really need
            2. Define clear scope, timeline, and deliverables
            3. Estimate total costs for this project
            4. Write a brief 'Scope Lock' summary
            5. Present everything clearly
            
            Focus on understanding the business context and expected outcomes.
            """,
            agent=self.manager,
            expected_output="Project scope, key questions answered, and cost estimate with clear next steps"
        )

        # Create analysis tasks
        research_task = Task(
            description=f"""
            Research the topic: {user_request}
            
            Provide comprehensive research including:
            - Market size and growth trends
            - Key players and competitive landscape
            - Recent developments and news
            - Regulatory environment
            - Investment trends and valuations
            
            Use live web research and provide citations.
            """,
            agent=self.researcher,
            expected_output="Comprehensive research report with citations and key data points"
        )

        data_task = Task(
            description="""
            Based on the research findings, identify and prepare relevant datasets:
            
            1. Find public data sources (Census, BLS, SEC filings, etc.)
            2. Plan data cleaning and structuring approach
            3. Create analysis methodology
            4. Document data sources and limitations
            
            Focus on data that supports market sizing and competitive analysis.
            """,
            agent=self.data_engineer,
            expected_output="Data analysis plan with sources and methodology documented"
        )

        viz_task = Task(
            description="""
            Create visualization concepts based on research and data:
            
            1. Market size and trend charts
            2. Competitive landscape mapping
            3. Key metrics dashboard concepts
            4. Executive summary visual framework
            
            Focus on clear, professional concepts suitable for executive presentation.
            """,
            agent=self.viz_analyst,
            expected_output="Visualization concepts and dashboard framework for executive presentation"
        )

        synthesis_task = Task(
            description="""
            Synthesize all findings into an executive-ready strategic memo:
            
            1. Executive summary with key findings
            2. Market opportunity assessment
            3. Strategic recommendations
            4. Risk analysis and considerations
            5. Recommended next steps
            
            Write in consulting memo format suitable for C-suite decision making.
            Reference specific data points and analysis from the team.
            """,
            agent=self.consultant,
            expected_output="Executive strategic memo with recommendations and supporting analysis"
        )
        return [scoping_task, research_task, data_task, viz_task, synthesis_task]

    def run_scope_analysis(self, user_request):
        tasks = self.create_tasks(user_request)
        scoping_task = tasks[0]

        crew = Crew(
            agents=[self.manager],
            tasks=[scoping_task],
            process=Process.sequential,
            verbose=True
        )

        print("🚀 Starting scoping analysis...")
        crew_output = crew.kickoff()
        result = crew_output.raw if hasattr(crew_output, "raw") else str(crew_output)
        return result

    def run_remaining_analysis(self, user_request, scoping_context):
        tasks = self.create_tasks(user_request)
        
        # Provide the output of the scoping task as context to the research task
        research_task = tasks[1]
        research_task.description = f"""
        Based on the following project scope, conduct your research.
        Project Scope: {scoping_context}
        
        Original research request: {user_request}
        
        Provide comprehensive research including:
        - Market size and growth trends
        - Key players and competitive landscape
        - Recent developments and news
        - Regulatory environment
        - Investment trends and valuations
        
        Use live web research and provide citations.
        """

        crew = Crew(
            agents=[self.researcher, self.data_engineer, self.viz_analyst, self.consultant],
            tasks=tasks[1:],
            process=Process.sequential,
            verbose=True
        )

        print("🚀 Starting remaining analysis...")
        crew_output = crew.kickoff()
        result = crew_output.raw if hasattr(crew_output, "raw") else str(crew_output)
        return result
