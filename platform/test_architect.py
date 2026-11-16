from src.core.project_loader import ProjectLoader
from src.agents.architect_agent import ArchitectAgent

loader = ProjectLoader()
agent = ArchitectAgent(loader, enable_2d_rendering=False, enable_3d_rendering=False)
agent.load_project('heritage_sanctuary')
output = agent.process()
print(output['results']['design_style'])
print(output['results']['cultural_elements'])