# executive_planner.py — High-Level Planning for Complex Tasks
"""
Executive Planner - Breaks down complex tasks into executable components.

Based on analysis of:
1. Senior Software Engineer - architectural thinking, decomposition
2. Entrepreneur/Investor - Warren Buffett, Charlie Munger style analysis

The key: High-level planning that most agents lack.
Decompose → Estimate → Execute → Review → Iterate

NOTE (2026-03-07):
- Mini-LLM runtime: Always-on local fast reasoning, no external API delay
- Nested stalks: Stalks within stalks - hierarchical structure
- Atomic nodules: Granularized nodes within stalks
- Fail up: When sub-stalk fails, escalate to parent
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import time


# =============================================================================
# SENIOR SOFTWARE ENGINEER - Task Decomposition
# =============================================================================

class TaskComplexity(Enum):
    """Task complexity levels."""
    TRIVIAL = 1   # < 1 hour
    SIMPLE = 2    # 1-4 hours
    MODERATE = 3  # 1-3 days
    COMPLEX = 4   # 1-2 weeks
    EPIC = 5      # 1+ month


@dataclass
class TechnicalSpec:
    """Technical specification for a task."""
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]
    dependencies: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    tradeoffs: List[str] = field(default_factory=list)


@dataclass
class TaskDecomposition:
    """Decomposed task with components."""
    id: str
    original_request: str
    
    # Analysis
    understanding: str
    assumptions: List[str]
    
    # Spec
    specs: List[TechnicalSpec]
    
    # Components
    components: List[str]
    
    # Estimation
    complexity: TaskComplexity
    estimated_hours: float
    risk_factors: List[str]
    
    # Architecture
    architecture_notes: str
    tech_stack: List[str] = field(default_factory=list)
    
    # Timeline
    milestones: List[Dict] = field(default_factory=list)


class SeniorEngineerPlanner:
    """
    Senior Software Engineer style planning.
    
    Decomposes complex requests into:
    - Understanding (what exactly do they want?)
    - Specifications (what, inputs, outputs)
    - Components (what needs building)
    - Architecture (how it fits together)
    - Estimation (how long, how risky)
    - Timeline (milestones)
    """
    
    def __init__(self):
        self.decompositions: List[TaskDecomposition] = []
        
        # Standard patterns to consider
        self.design_patterns = [
            "MVC", "Repository", "Factory", "Observer", "Strategy",
            "Adapter", "Decorator", "Singleton", "Builder", "Prototype"
        ]
        
        self.architecture_styles = [
            "Microservices", "Monolith", "Event-driven", "Layered",
            "Hexagonal", "Clean", "Serverless", "GraphQL"
        ]
    
    def decompose(self, request: str, context: Dict = None) -> TaskDecomposition:
        """
        Decompose a complex request into executable components.
        
        Args:
            request: The original request
            context: Additional context
            
        Returns:
            TaskDecomposition
        """
        decomposition = TaskDecomposition(
            id=f"decomp_{time.time()}",
            original_request=request,
            understanding="",
            assumptions=[],
            specs=[],
            components=[],
            complexity=TaskComplexity.MODERATE,
            estimated_hours=0.0,
            risk_factors=[],
            architecture_notes=""
        )
        
        # Step 1: Understand the request
        decomposition.understanding = self._understand_request(request, context)
        
        # Step 2: Identify assumptions
        decomposition.assumptions = self._identify_assumptions(request, context)
        
        # Step 3: Create specs
        decomposition.specs = self._create_specs(request, context)
        
        # Step 4: Decompose into components
        decomposition.components = self._decompose_components(request, context)
        
        # Step 5: Architecture decisions
        decomposition.architecture_notes, decomposition.tech_stack = self._decide_architecture(
            request, context
        )
        
        # Step 6: Estimate
        decomposition.complexity, decomposition.estimated_hours = self._estimate(
            decomposition.components, decomposition.specs
        )
        
        # Step 7: Identify risks
        decomposition.risk_factors = self._identify_risks(
            decomposition.components, decomposition.specs
        )
        
        # Step 8: Create timeline
        decomposition.milestones = self._create_milestones(
            decomposition.components, decomposition.estimated_hours
        )
        
        self.decompositions.append(decomposition)
        return decomposition
    
    def _understand_request(self, request: str, context: Dict) -> str:
        """Understand what the user actually wants."""
        # In production: use LLM to analyze
        # Here: simple heuristic
        words = request.lower().split()
        
        if "build" in words or "create" in words or "make" in words:
            return "Build/create something new"
        elif "fix" in words or "bug" in words or "error" in words:
            return "Fix existing issue"
        elif "improve" in words or "optimize" in words:
            return "Improve existing system"
        elif "understand" in words or "analyze" in words:
            return "Analyze existing system"
        else:
            return "General task"
    
    def _identify_assumptions(self, request: str, context: Dict) -> List[str]:
        """Identify what we're assuming."""
        assumptions = []
        
        # Common assumptions
        if context:
            if "language" not in context:
                assumptions.append("Language/framework not specified")
            if "platform" not in context:
                assumptions.append("Platform not specified")
        
        return assumptions
    
    def _create_specs(self, request: str, context: Dict) -> List[TechnicalSpec]:
        """Create technical specifications."""
        # Would use LLM in production
        # Simple: one spec per major component
        
        spec = TechnicalSpec(
            name="main",
            description=request,
            inputs=["user input"],
            outputs=["result"],
            dependencies=[],
            patterns=[],
            tradeoffs=["time vs quality"]
        )
        
        return [spec]
    
    def _decompose_components(self, request: str, context: Dict) -> List[str]:
        """Break into components."""
        components = []
        
        # Always need these for any software
        components.append("core_logic")
        components.append("data_layer")
        components.append("api_interface")
        
        # Add based on request
        request_lower = request.lower()
        
        if "user" in request_lower or "auth" in request_lower:
            components.append("authentication")
        if "real" in request_lower or "live" in request_lower:
            components.append("realtime_updates")
        if "data" in request_lower or "report" in request_lower:
            components.append("data_processing")
        if "ui" in request_lower or "interface" in request_lower:
            components.append("frontend")
        
        # Always add
        components.append("tests")
        components.append("documentation")
        
        return components
    
    def _decide_architecture(self, request: str, context: Dict) -> tuple:
        """Decide on architecture."""
        # Simple decision tree
        request_lower = request.lower()
        
        if "microservice" in request_lower:
            return "Microservices architecture", ["Kubernetes", "Docker", "API Gateway"]
        elif "simple" in request_lower or "small" in request_lower:
            return "Simple monolith", ["Flask", "SQLite"]
        else:
            return "Clean architecture", ["Python", "PostgreSQL", "React"]
    
    def _estimate(self, components: List[str], specs: List[TechnicalSpec]) -> tuple:
        """Estimate complexity and time."""
        base_hours = len(components) * 4  # 4 hours per component
        
        # Adjust for complexity
        if len(components) > 10:
            complexity = TaskComplexity.COMPLEX
            multiplier = 2.0
        elif len(components) > 5:
            complexity = TaskComplexity.MODERATE
            multiplier = 1.5
        else:
            complexity = TaskComplexity.SIMPLE
            multiplier = 1.0
        
        return complexity, base_hours * multiplier
    
    def _identify_risks(self, components: List[str], specs: List[TechnicalSpec]) -> List[str]:
        """Identify risk factors."""
        risks = []
        
        # Always consider
        risks.append("Requirements may change")
        risks.append("Hidden complexity in dependencies")
        
        # Component-specific
        if "realtime" in components:
            risks.append("Real-time systems are hard")
        if "data" in components:
            risks.append("Data migration/quality issues")
        
        return risks
    
    def _create_milestones(self, components: List[str], hours: float) -> List[Dict]:
        """Create timeline milestones."""
        milestones = []
        
        # Split into phases
        phase_size = len(components) // 3
        
        if phase_size > 0:
            milestones.append({
                "name": "Foundation",
                "components": components[:phase_size],
                "percentage": 33
            })
            milestones.append({
                "name": "Core",
                "components": components[phase_size:phase_size*2],
                "percentage": 33
            })
            milestones.append({
                "name": "Polish",
                "components": components[phase_size*2:],
                "percentage": 34
            })
        
        return milestones


# =============================================================================
# INVESTOR/ENTREPRENEUR - Business Analysis
# =============================================================================

@dataclass
class BusinessAnalysis:
    """Analysis of a business/investment opportunity."""
    id: str
    name: str
    
    # Buffett/Munger style analysis
    business_description: str
    moat: str  # Competitive advantage
    unit_economics: Dict  # LTV, CAC, margins
    management: str  # Quality of leadership
    risk_factors: List[str]
    opportunity: str  # Why mispriced?
    
    # Analysis
    intrinsic_value_estimate: float = 0.0
    margin_of_safety: float = 0.0
    recommendation: str = ""  # buy/hold/sell
    time_horizon: str = "10 years"
    
    # Source materials
    sources_analyzed: List[str] = field(default_factory=list)


@dataclass
class PortfolioPosition:
    """A position in portfolio."""
    name: str
    allocation: float  # Percentage
    thesis: str  # Why we own it
    risk: float  # 0-1
    expected_return: float


class InvestorPlanner:
    """
    Warren Buffett / Charlie Munger style analysis.
    
    Analyzes businesses and opportunities:
    - What does the business do?
    - What's the moat?
    - Unit economics?
    - Management quality?
    - Long-term opportunity?
    - Risk factors?
    - Intrinsic value?
    """
    
    def __init__(self):
        self.analyses: List[BusinessAnalysis] = []
        self.portfolio: List[PortfolioPosition] = []
        
        # Munger's mental models
        self.mental_models = [
            "Margin of Safety",
            "Circle of Competence",
            "Mr. Market",
            "Baker's Dozen",
            "Inversion",
            "Second-Order Thinking",
            "Economics of Moats",
            "Risk/Return Asymmetry"
        ]
    
    def analyze_business(self, name: str, description: str, 
                       sources: List[str] = None) -> BusinessAnalysis:
        """
        Analyze a business/investment opportunity.
        
        Args:
            name: Business name
            description: What the business does
            sources: Annual reports, Buffett letters, etc.
            
        Returns:
            BusinessAnalysis
        """
        analysis = BusinessAnalysis(
            id=f"analysis_{time.time()}",
            name=name,
            business_description=description,
            moat="",
            unit_economics={},
            management="",
            risk_factors=[],
            opportunity="",
            sources_analyzed=sources or []
        )
        
        # Analyze moat
        analysis.moat = self._analyze_moat(description)
        
        # Unit economics
        analysis.unit_economics = self._analyze_unit_economics(description)
        
        # Management (would read letters/reports in production)
        analysis.management = "TBD - need annual meeting notes"
        
        # Risk factors
        analysis.risk_factors = self._identify_risks(description)
        
        # Opportunity
        analysis.opportunity = self._find_opportunity(description)
        
        # Estimate intrinsic value (simplified)
        analysis.intrinsic_value_estimate = self._estimate_intrinsic_value(analysis)
        analysis.margin_of_safety = 0.3  # Target 30% margin
        
        # Recommendation
        analysis.recommendation = self._make_recommendation(analysis)
        
        self.analyses.append(analysis)
        return analysis
    
    def _analyze_moat(self, description: str) -> str:
        """Analyze competitive advantage."""
        desc_lower = description.lower()
        
        if "network" in desc_lower or "platform" in desc_lower:
            return "Network effect moat"
        elif "brand" in desc_lower:
            return "Brand moat"
        elif "cost" in desc_lower or "cheap" in desc_lower:
            return "Cost advantage moat"
        elif "switch" in desc_lower or "lock" in desc_lower:
            return "Switching cost moat"
        elif "data" in desc_lower:
            return "Data moat"
        else:
            return "Unknown moat - need deeper analysis"
    
    def _analyze_unit_economics(self, description: str) -> Dict:
        """Analyze unit economics."""
        # Simplified - would need real data
        return {
            "revenue_per_customer": "TBD",
            "cost_to_serve": "TBD",
            "margin": "TBD",
            "cac": "TBD",
            "ltv": "TBD"
        }
    
    def _identify_risks(self, description: str) -> List[str]:
        """Identify risk factors."""
        risks = []
        
        desc_lower = description.lower()
        
        if "regulation" in desc_lower or "legal" in desc_lower:
            risks.append("Regulatory risk")
        if "technology" in desc_lower or "tech" in desc_lower:
            risks.append("Technology disruption")
        if "debt" in desc_lower:
            risks.append("Financial risk")
        if "competition" in desc_lower or "competitor" in desc_lower:
            risks.append("Competitive pressure")
        
        # General
        risks.append("Management execution risk")
        risks.append("Macroeconomic risk")
        
        return risks
    
    def _find_opportunity(self, description: str) -> str:
        """Find the opportunity/mispricing."""
        # What does this business do that others don't?
        # What's undervalued?
        return "Need to analyze annual reports and compare to market perception"
    
    def _estimate_intrinsic_value(self, analysis: BusinessAnalysis) -> float:
        """Estimate intrinsic value."""
        # Simplified DCF - would be more complex in production
        return 0.0  # Need financial data
    
    def _make_recommendation(self, analysis: BusinessAnalysis) -> str:
        """Make investment recommendation."""
        # Based on analysis
        if analysis.moat and analysis.moat != "Unknown moat":
            if analysis.risk_factors:
                return "HOLD - Good business but need more margin of safety"
            else:
                return "BUY - Strong moat, manageable risks"
        else:
            return "PASS - Moat unclear, need more research"
    
    def add_to_portfolio(self, analysis: BusinessAnalysis, allocation: float):
        """Add position to portfolio."""
        position = PortfolioPosition(
            name=analysis.name,
            allocation=allocation,
            thesis=f"Moat: {analysis.moat}",
            risk=0.5,
            expected_return=0.10
        )
        self.portfolio.append(position)
    
    def get_portfolio_risk(self) -> float:
        """Get overall portfolio risk."""
        if not self.portfolio:
            return 0.0
        return sum(p.risk * p.allocation for p in self.portfolio) / 100.0


# =============================================================================
# EXECUTIVE PLANNER - Combined High-Level Planning
# =============================================================================

class ExecutivePlanner:
    """
    Combined planner for software and business tasks.
    
    This is what most agents lack - the ability to:
    1. Understand complex requests
    2. Break into executable components
    3. Estimate effort/timeline
    4. Identify risks
    5. Create milestones
    6. Execute with feedback
    
    Works for:
    - Software engineering tasks
    - Business analysis
    - Investment decisions
    - Enterprise building
    """
    
    def __init__(self):
        self.software_planner = SeniorEngineerPlanner()
        self.investor_planner = InvestorPlanner()
        
        # Task history
        self.tasks: List[Dict] = []
    
    def plan(self, task_type: str, request: str, context: Dict = None) -> Dict:
        """
        Create a high-level plan.
        
        Args:
            task_type: "software", "business", "investment"
            request: The task request
            context: Additional context
            
        Returns:
            Plan dictionary
        """
        if task_type == "software":
            decomposition = self.software_planner.decompose(request, context)
            plan = {
                "type": "software",
                "task_id": decomposition.id,
                "understanding": decomposition.understanding,
                "components": decomposition.components,
                "architecture": decomposition.architecture_notes,
                "tech_stack": decomposition.tech_stack,
                "complexity": decomposition.complexity.name,
                "estimated_hours": decomposition.estimated_hours,
                "risk_factors": decomposition.risk_factors,
                "milestones": decomposition.milestones
            }
        elif task_type == "business" or task_type == "investment":
            analysis = self.investor_planner.analyze_business(
                name=request.split()[0],  # First word as name
                description=request,
                sources=context.get("sources") if context else None
            )
            plan = {
                "type": "investment",
                "analysis_id": analysis.id,
                "business": analysis.name,
                "moat": analysis.moat,
                "risks": analysis.risk_factors,
                "opportunity": analysis.opportunity,
                "recommendation": analysis.recommendation,
                "time_horizon": analysis.time_horizon
            }
        else:
            plan = {"type": "unknown", "error": "Unknown task type"}
        
        self.tasks.append(plan)
        return plan
    
    def get_task_history(self) -> List[Dict]:
        """Get task history."""
        return self.tasks


# Example usage
if __name__ == "__main__":
    planner = ExecutivePlanner()
    
    # Software planning
    print("=== Software Planning ===")
    software_plan = planner.plan(
        "software",
        "Build a real-time chat application with user authentication"
    )
    print(f"Components: {software_plan['components']}")
    print(f"Complexity: {software_plan['complexity']}")
    print(f"Estimate: {software_plan['estimated_hours']} hours")
    print(f"Architecture: {software_plan['architecture']}")
    
    # Business analysis
    print("\n=== Business Analysis ===")
    business_plan = planner.plan(
        "investment",
        "Apple Inc - consumer electronics and services company"
    )
    print(f"Business: {business_plan['business']}")
    print(f"Moat: {business_plan['moat']}")
    print(f"Recommendation: {business_plan['recommendation']}")
    print(f"Time horizon: {business_plan['time_horizon']}")
