"""
Base Agent Class for FiveHorses Platform
All agents inherit from this base class to access project data and knowledge
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from src.core.project_loader import ProjectLoader
from src.knowledge.knowledge_loader import KnowledgeLoader


class BaseAgent:
    """
    Base class for all FiveHorses agents
    
    Provides:
    - Access to project data via ProjectLoader
    - Access to knowledge via KnowledgeLoader
    - Standardized output format
    - Logging functionality
    """
    
    def __init__(self, project_loader: Optional[ProjectLoader] = None):
        """
        Initialize the agent
        
        Args:
            project_loader: ProjectLoader instance to use
        """
        self.project_loader = project_loader or ProjectLoader()
        self.knowledge = KnowledgeLoader()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Agent metadata
        self.agent_name = self.__class__.__name__
        self.agent_version = "1.0"
        self.agent_description = self.__doc__ or "No description provided"
        
        self._project_data = None
    
    @property
    def project_data(self) -> Dict[str, Any]:
        """Get the current project data"""
        if self._project_data is None and self.project_loader.current_project is None:
            raise ValueError("No project loaded. Call load_project() first.")
        elif self._project_data is None:
            self._project_data = self.project_loader.current_project
        return self._project_data
    
    def load_project(self, project_name: str) -> None:
        """
        Load a project by name
        
        Args:
            project_name: Name of the project to load
        """
        self._project_data = self.project_loader.load_project(project_name)
        self.logger.info(f"Loaded project: {project_name}")
    
    def get_project_data(self, path: str) -> Any:
        """
        Get specific project data using dot notation
        
        Args:
            path: Dot notation path (e.g., "project.site_area_ha")
            
        Returns:
            Value at the specified path
        """
        return self.project_loader.get_data(path)
    
    def process(self) -> Dict[str, Any]:
        """
        Main processing method - overridden by subclasses
        
        Returns:
            Dictionary containing agent outputs
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def format_output(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the agent output in a standardized way
        
        Args:
            results: Raw results from processing
            
        Returns:
            Formatted output dictionary
        """
        return {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "agent_description": self.agent_description,
            "project_name": self.project_loader.current_project_name,
            "status": "success",
            "results": results
        }
    
    def validate_inputs(self) -> bool:
        """
        Validate that required inputs are present
        
        Returns:
            True if all required inputs are present
        """
        return True
    
    def get_required_inputs(self) -> list:
        """
        Get list of required input paths
        
        Returns:
            List of required input paths in dot notation
        """
        return []
    
    def save_output(self, output: Dict[str, Any], output_dir: Optional[Path] = None) -> Path:
        """
        Save agent output to file
        
        Args:
            output: Agent output dictionary
            output_dir: Directory to save output
            
        Returns:
            Path to saved file
        """
        if output_dir is None:
            # Save in project directory
            if self.project_loader.current_project_name is not None:
                output_dir = self.project_loader.projects_root / self.project_loader.current_project_name / "outputs"
            else:
                output_dir = Path("outputs")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = output_dir / f"{self.agent_name.lower()}_output.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        self.logger.info(f"Saved output to: {filename}")
        return filename