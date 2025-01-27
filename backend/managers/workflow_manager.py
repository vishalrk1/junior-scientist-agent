import asyncio
import pickle
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from buddy.model import load_model
from buddy.agents import AdviseAgent, AnalyzerAgent, PlannerAgent
from models.project import Project, ProjectStatus
from models.conversation import Conversation, Message, MessageType
from models.agent import Agent, AgentType
from models.report import Report
from database import Database
from .context_manager import ContextManager

class WorkflowManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project: Optional[Project] = None
        self.conversation: Optional[Conversation] = None
        self.agents: Dict[AgentType, Agent] = {}
        self.report_path = Path("reports")
        self.report_path.mkdir(exist_ok=True)
        self.context_manager = ContextManager(project_id)

    async def initialize(self):
        """Initialize workflow with project data and agents"""
        # Load project
        projects_coll = Database.get_projects_collection()
        self.project = await projects_coll.find_one({"_id": self.project_id})
        if not self.project:
            raise ValueError(f"Project {self.project_id} not found")

        # Initialize or load conversation
        conv_coll = await Database.get_collection("conversations")
        if self.project.current_conversation_id:
            self.conversation = await conv_coll.find_one({"_id": self.project.current_conversation_id})
        if not self.conversation:
            self.conversation = await self._create_conversation()

        # Initialize agents
        await self._initialize_agents()

    async def _create_conversation(self) -> Conversation:
        """Create a new conversation for the project"""
        conv = Conversation(
            project_id=self.project_id,
            messages=[],
            active_agents=[],
            context_size=self.project.settings.get("context_size", 10)
        )
        conv_coll = await Database.get_collection("conversations")
        result = await conv_coll.insert_one(conv.dict())
        conv.id = str(result.inserted_id)
        
        # Update project with new conversation
        projects_coll = Database.get_projects_collection()
        await projects_coll.update_one(
            {"_id": self.project_id},
            {"$set": {"current_conversation_id": conv.id}}
        )
        return conv

    async def _initialize_agents(self):
        """Initialize all required agents for the project"""
        model = load_model(self.project.api_key)
        agents_coll = Database.get_agents_collection()
        
        for agent_type in AgentType:
            agent_config = await agents_coll.find_one({
                "project_id": self.project_id,
                "type": agent_type,
                "is_default": True
            })
            if not agent_config:
                continue
            
            self.agents[agent_type] = Agent(**agent_config)

    def _get_report_path(self, agent_type: AgentType) -> Path:
        """Get report file path for specific agent"""
        return self.report_path / f"{self.project_id}_{agent_type.value}_report.pkl"

    async def _save_report(
        self, 
        content: Any, 
        agent_type: AgentType,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Save report to both filesystem and database"""
        # Save to filesystem
        report_path = self._get_report_path(agent_type)
        with open(report_path, 'wb') as f:
            pickle.dump(content, f)

        # Create report record in database
        report = Report(
            project_id=self.project_id,
            agent_type=agent_type,
            file_path=str(report_path),
            metadata=metadata or {},
            conversation_id=self.conversation.id
        )
        
        reports_coll = await Database.get_collection("reports")
        result = await reports_coll.insert_one(report.dict())
        
        # Update project with report reference
        await Database.get_projects_collection().update_one(
            {"_id": self.project_id},
            {"$push": {"report_ids": str(result.inserted_id)}}
        )
        
        return str(result.inserted_id)

    async def run_analysis(self, dataset_path: str) -> str:
        """Run data analysis workflow"""
        analyzer = self.agents.get(AgentType.analyzer)
        if not analyzer:
            raise ValueError("Analyzer agent not configured")

        # Add message to conversation
        message = Message(
            type=MessageType.analyzer,
            content=f"Starting analysis of dataset: {dataset_path}",
            agent_id=str(analyzer.id)
        )
        await self._add_message(message)

        try:
            report = await self._run_agent_task(
                agent_type=AgentType.analyzer,
                method="analyze_data",
                dataset_path=dataset_path
            )
            
            report_id = await self._save_report(
                content=report,
                agent_type=AgentType.analyzer,
                metadata={"dataset_path": dataset_path}
            )
            
            success_msg = Message(
                type=MessageType.analyzer,
                content="Analysis completed successfully",
                agent_id=str(analyzer.id),
                metadata={"report_path": str(self.report_path)}
            )
            await self._add_message(success_msg)

            return str(self.report_path)

        except Exception as e:
            error_msg = Message(
                type=MessageType.analyzer,
                content=f"Analysis failed: {str(e)}",
                agent_id=str(analyzer.id)
            )
            await self._add_message(error_msg)
            raise

    async def get_advice(self, requirements: str) -> str:
        """Get ML advice based on analysis results"""
        advisor = self.agents.get(AgentType.advisor)
        if not advisor:
            raise ValueError("Advisor agent not configured")

        message = Message(
            type=MessageType.advisor,
            content=f"Processing requirements: {requirements}",
            agent_id=str(advisor.id)
        )
        await self._add_message(message)

        try:
            advice = await self._run_agent_task(
                agent_type=AgentType.advisor,
                method="suggest",
                requirements=requirements
            )

            success_msg = Message(
                type=MessageType.advisor,
                content=advice,
                agent_id=str(advisor.id)
            )
            await self._add_message(success_msg)
            return advice

        except Exception as e:
            error_msg = Message(
                type=MessageType.advisor,
                content=f"Failed to generate advice: {str(e)}",
                agent_id=str(advisor.id)
            )
            await self._add_message(error_msg)
            raise

    async def generate_plan(self) -> str:
        """Generate ML development plan"""
        planner = self.agents.get(AgentType.planner)
        if not planner:
            raise ValueError("Planner agent not configured")

        message = Message(
            type=MessageType.planner,
            content="Generating ML development plan",
            agent_id=str(planner.id)
        )
        await self._add_message(message)

        try:
            plan = await self._run_agent_task(
                agent_type=AgentType.planner,
                method="generate_plan"
            )

            success_msg = Message(
                type=MessageType.planner,
                content=plan,
                agent_id=str(planner.id)
            )
            await self._add_message(success_msg)
            return plan

        except Exception as e:
            error_msg = Message(
                type=MessageType.planner,
                content=f"Failed to generate plan: {str(e)}",
                agent_id=str(planner.id)
            )
            await self._add_message(error_msg)
            raise

    async def _add_message(self, message: Message):
        """Add message to conversation and persist"""
        self.conversation.messages.append(message)
        conv_coll = await Database.get_collection("conversations")
        await conv_coll.update_one(
            {"_id": self.conversation.id},
            {"$push": {"messages": message.dict()}}
        )
        await self.context_manager.update_context(message, self.conversation.id)

    async def _run_agent_task(self, agent_type: AgentType, method: str, **kwargs):
        """Run agent task with context"""
        agent = self.agents.get(agent_type)
        if not agent:
            raise ValueError(f"Agent {agent_type} not found")

        # Get context for agent
        context = await self.context_manager.get_agent_context(
            agent_type,
            self.conversation.id
        )

        # Get agent class based on type
        agent_classes = {
            AgentType.analyzer: AnalyzerAgent,
            AgentType.advisor: AdviseAgent,
            AgentType.planner: PlannerAgent
        }

        agent_class = agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Create agent instance with context
        model = load_model(self.project.api_key)
        agent_instance = agent_class(
            model,
            config=agent.parameters,
            context=context
        )

        # Run method in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: getattr(agent_instance, method)(**kwargs)
        )
        return result
