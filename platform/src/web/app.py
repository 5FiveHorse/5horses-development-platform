"""
FiveHorses Web Application - Complete Multi-Agent Version
FastAPI server with web form, dashboard, and all 5 agents integrated
"""

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
from datetime import datetime
from typing import Optional

from src.core.project_loader import ProjectLoader
from src.core.schema_validator import ProjectSchemaValidator
from src.agents import AgentOrchestrator

# Initialize FastAPI
def money(v):
    """Doctrine A7: redacted (None) renders as em-dash, never a fabricated 0."""
    return f"${v:,.2f}" if isinstance(v, (int, float)) else "\u2014"
def qty(v):
    """Integer-with-commas, or em-dash when withheld."""
    return f"{v:,.0f}" if isinstance(v, (int, float)) else "\u2014"
def pct_share(part, total):
    """Percentage of total; em-dash when either side is withheld or total<=0."""
    if not isinstance(part, (int, float)):
        return "\u2014"
    if not isinstance(total, (int, float)) or total <= 0:
        return "\u2014"
    return f"{part / total * 100:.1f}"
def dash(v, fallback="\u2014"):
    """Pass through any value; withheld (None) becomes the fallback."""
    return fallback if v is None else v
app = FastAPI(title="FiveHorses Property Development Platform")

# Setup paths
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "css").mkdir(exist_ok=True)
(STATIC_DIR / "js").mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize project loader
loader = ProjectLoader()

# ============ HELPER FUNCTIONS ============

def format_currency(value):
    """Format a number as Australian currency"""
    if value is None:
        return "$0.00"
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def format_number(value):
    """Format a number with commas"""
    if value is None:
        return "0"
    try:
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return "0"

# ============ HTML TEMPLATES ============

def get_base_html(title, content, scripts=""):
    """Generate base HTML template"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - FiveHorses Platform</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #1a2a6c, #2d4373);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 1.5rem; font-weight: 600; }}
        .header h1 span {{ color: #ffd700; }}
        .nav a {{
            color: white;
            text-decoration: none;
            margin-left: 2rem;
            padding: 0.5rem 1rem;
            border-radius: 4px;
        }}
        .nav a:hover {{ background: rgba(255,255,255,0.1); }}
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }}
        .card h2 {{ margin-bottom: 1rem; color: #1a2a6c; }}
        .card h3 {{ margin-bottom: 0.75rem; color: #2d4373; }}
        .btn {{
            display: inline-block;
            background: #1a2a6c;
            color: white;
            padding: 0.5rem 1.5rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 0.9rem;
        }}
        .btn:hover {{ background: #2d4373; }}
        .btn-success {{ background: #28a745; }}
        .btn-success:hover {{ background: #218838; }}
        .btn-danger {{ background: #dc3545; }}
        .btn-danger:hover {{ background: #c82333; }}
        .btn-primary {{ background: #007bff; }}
        .btn-primary:hover {{ background: #0056b3; }}
        .btn-secondary {{ background: #6c757d; }}
        .btn-secondary:hover {{ background: #5a6268; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        .metric-card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid #1a2a6c;
        }}
        .metric-card .label {{ font-size: 0.85rem; color: #666; text-transform: uppercase; font-weight: 600; }}
        .metric-card .value {{ font-size: 1.5rem; font-weight: 700; margin-top: 0.25rem; }}
        .metric-card .value.positive {{ color: #28a745; }}
        .metric-card .value.negative {{ color: #dc3545; }}
        .form-group {{ margin-bottom: 1rem; }}
        .form-group label {{ display: block; font-weight: 600; margin-bottom: 0.25rem; font-size: 0.9rem; }}
        .form-group input, .form-group select, .form-group textarea {{
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.9rem;
        }}
        .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
        .alert {{
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }}
        .alert-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .alert-danger {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .alert-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
        .alert-info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
        .flex {{ display: flex; justify-content: space-between; align-items: center; }}
        .gap-2 {{ gap: 0.5rem; }}
        .mt-2 {{ margin-top: 1rem; }}
        .mt-3 {{ margin-top: 1.5rem; }}
        .mb-2 {{ margin-bottom: 1rem; }}
        .text-muted {{ color: #666; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th, .table td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #dee2e6; }}
        .table th {{ background: #f8f9fa; font-weight: 600; }}
        .table tr:hover {{ background: #f8f9fa; }}
        .project-list-item {{
            padding: 1rem;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }}
        .project-list-item:hover {{ background: #f8f9fa; }}
        .project-list-item .name {{ font-weight: 600; font-size: 1.1rem; }}
        .project-list-item .details {{ font-size: 0.9rem; color: #666; }}
        .upload-area {{
            border: 2px dashed #ddd;
            padding: 2rem;
            text-align: center;
            border-radius: 8px;
        }}
        .upload-area:hover {{ border-color: #1a2a6c; }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-info {{ background: #d1ecf1; color: #0c5460; }}
        .text-center {{ text-align: center; }}
        .text-right {{ text-align: right; }}
        .agent-status {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .agent-status.success {{ background: #d4edda; color: #155724; }}
        .agent-status.failed {{ background: #f8d7da; color: #721c24; }}
        .tab {{
            overflow: hidden;
            border-bottom: 1px solid #dee2e6;
            margin-bottom: 1rem;
        }}
        .tab button {{
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 0.75rem 1.5rem;
            transition: 0.3s;
            font-size: 0.9rem;
            background: transparent;
            font-weight: 600;
            color: #666;
        }}
        .tab button:hover {{ background: #f8f9fa; }}
        .tab button.active {{
            color: #1a2a6c;
            border-bottom: 3px solid #1a2a6c;
        }}
        .tabcontent {{
            display: none;
            animation: fadeEffect 0.5s;
        }}
        .tabcontent.active {{ display: block; }}
        @keyframes fadeEffect {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1>🏇 Five<span>Horses</span></h1>
            <nav class="nav">
                <a href="/">Projects</a>
                <a href="/project/new">New Project</a>
            </nav>
        </div>
    </header>
    <div class="container">
        {content}
    </div>
    <script>
        function formatCurrency(amount) {{
            return new Intl.NumberFormat('en-AU', {{ style: 'currency', currency: 'AUD' }}).format(amount);
        }}
        function formatNumber(num) {{
            return new Intl.NumberFormat('en-AU').format(num);
        }}
        {scripts}
    </script>
</body>
</html>"""

# ============ ROUTES ============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with project list"""
    projects = loader.list_projects()
    
    # Build project list HTML
    projects_html = ""
    if projects:
        for project in projects:
            projects_html += f"""
            <div class="project-list-item">
                <div class="flex">
                    <div>
                        <div class="name">{project['name']}</div>
                        <div class="details">
                            Type: {project['type']} | Location: {project['location']}
                            {f' | Updated: {project["last_updated"]}' if project.get('last_updated') != 'unknown' else ''}
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <a href="/project/{project['name']}" class="btn btn-primary">View Dashboard</a>
                        <button class="btn btn-danger" onclick="deleteProject('{project['name']}')">Delete</button>
                    </div>
                </div>
            </div>
            """
    else:
        projects_html = '<p class="text-muted">No projects yet. Create your first project!</p>'
    
    content = f"""
    <div class="flex">
        <h2>📋 Projects</h2>
        <a href="/project/new" class="btn btn-success">+ New Project</a>
    </div>
    
    <div class="card">
        <h2>Upload Project JSON</h2>
        <div class="upload-area" id="uploadArea">
            <p>📁 Drop your project_data.json here or click to upload</p>
            <input type="file" id="fileInput" accept=".json" style="display: none;">
            <button class="btn btn-primary mt-2" onclick="document.getElementById('fileInput').click()">Choose File</button>
            <div id="uploadStatus" class="mt-2"></div>
        </div>
    </div>
    
    <div class="card">
        <h2>Your Projects</h2>
        {projects_html}
    </div>
    """
    
    scripts = """
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#1a2a6c';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#ddd';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#ddd';
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    function handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);
        uploadStatus.innerHTML = 'Uploading...';
        fetch('/api/project/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                uploadStatus.innerHTML = `<div class="alert alert-success">✅ Project '${data.project_name}' uploaded successfully! <a href="/project/${data.project_name}" class="btn btn-primary">View Project</a></div>`;
                setTimeout(() => location.reload(), 3000);
            } else {
                uploadStatus.innerHTML = `<div class="alert alert-danger">❌ Error: ${data.message || 'Upload failed'}</div>`;
            }
        })
        .catch(error => {
            uploadStatus.innerHTML = `<div class="alert alert-danger">❌ Error: ${error.message}</div>`;
        });
    }
    
    function deleteProject(projectName) {
        if (!confirm(`Are you sure you want to delete "${projectName}"?`)) return;
        fetch(`/api/project/${projectName}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') location.reload();
            else alert('Error deleting project: ' + data.message);
        })
        .catch(error => alert('Error: ' + error.message));
    }
    """
    
    return HTMLResponse(content=get_base_html("FiveHorses Platform", content, scripts))

@app.get("/project/new", response_class=HTMLResponse)
async def new_project_form(request: Request):
    """Form to create a new project"""
    content = """
    <div class="flex">
        <h2>📝 New Project</h2>
        <a href="/" class="btn btn-secondary">← Back to Projects</a>
    </div>
    
    <div class="card">
        <form method="POST" action="/project/save" id="projectForm">
            <h3>Project Details</h3>
            <div class="form-row">
                <div class="form-group">
                    <label for="project_name">Project Name *</label>
                    <input type="text" id="project_name" name="project_name" required placeholder="e.g., Gnowangerup Housing">
                </div>
                <div class="form-group">
                    <label for="project_type">Project Type *</label>
                    <select id="project_type" name="project_type" required>
                        <option value="community_housing">Community Housing</option>
                        <option value="social_housing">Social Housing</option>
                        <option value="commercial">Commercial</option>
                        <option value="traditional">Traditional</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="location">Location *</label>
                    <input type="text" id="location" name="location" required placeholder="e.g., gnowangerup">
                </div>
                <div class="form-group">
                    <label for="site_area_ha">Site Area (hectares) *</label>
                    <input type="number" id="site_area_ha" name="site_area_ha" required step="0.01" min="0.01" placeholder="17.18">
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="land_tenure">Land Tenure</label>
                    <select id="land_tenure" name="land_tenure">
                        <option value="freehold">Freehold</option>
                        <option value="leasehold">Leasehold</option>
                        <option value="peppercorn_lease" selected>Peppercorn Lease</option>
                        <option value="state_reserve">State Reserve</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="land_cost">Land Cost ($)</label>
                    <input type="number" id="land_cost" name="land_cost" step="1" min="0" value="0">
                </div>
            </div>
            
            <div class="form-group">
                <label for="description">Site Description</label>
                <textarea id="description" name="description" rows="3" placeholder="Describe the site..."></textarea>
            </div>
            
            <hr class="mt-2 mb-2">
            
            <h3>Dwellings</h3>
            <div id="dwellings-container">
                <div class="form-row dwelling-row">
                    <div class="form-group">
                        <label>Type</label>
                        <input type="text" class="dwelling-type" placeholder="e.g., 3x2" value="3x2">
                    </div>
                    <div class="form-group">
                        <label>Count</label>
                        <input type="number" class="dwelling-count" min="1" value="2">
                    </div>
                    <div class="form-group">
                        <label>Bedrooms</label>
                        <input type="number" class="dwelling-bedrooms" min="0" value="3">
                    </div>
                    <div class="form-group">
                        <label>Bathrooms</label>
                        <input type="number" class="dwelling-bathrooms" min="0" step="0.5" value="2">
                    </div>
                    <div class="form-group">
                        <label>Area (sqm)</label>
                        <input type="number" class="dwelling-area" min="20" value="140">
                    </div>
                    <div class="form-group" style="display: flex; align-items: flex-end;">
                        <button type="button" class="btn btn-danger remove-dwelling" style="padding: 0.5rem;">×</button>
                    </div>
                </div>
            </div>
            <button type="button" class="btn btn-secondary" onclick="addDwelling()">+ Add Dwelling</button>
            
            <hr class="mt-2 mb-2">
            
            <h3>Costs</h3>
            <div class="form-row">
                <div class="form-group">
                    <label for="planning_cost">Planning Cost ($)</label>
                    <input type="number" id="planning_cost" name="planning_cost" step="1" min="0" value="800000">
                </div>
                <div class="form-group">
                    <label for="infrastructure_cost">Infrastructure Cost ($)</label>
                    <input type="number" id="infrastructure_cost" name="infrastructure_cost" step="1" min="0" value="2300000">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label for="construction_cost">Construction Cost ($)</label>
                    <input type="number" id="construction_cost" name="construction_cost" step="1" min="0" value="4000000">
                </div>
                <div class="form-group">
                    <label for="management_cost">Project Management Cost ($)</label>
                    <input type="number" id="management_cost" name="management_cost" step="1" min="0" value="300000">
                </div>
            </div>
            <div class="form-group">
                <label for="contingency_percent">Contingency (%)</label>
                <input type="number" id="contingency_percent" name="contingency_percent" step="0.5" min="0" max="30" value="10">
            </div>
            
            <hr class="mt-2 mb-2">
            
            <h3>Funding Sources</h3>
            <div id="funding-container">
                <div class="form-row funding-row">
                    <div class="form-group">
                        <label>Source</label>
                        <input type="text" class="funding-source" placeholder="e.g., Government Grant" value="Government Grant">
                    </div>
                    <div class="form-group">
                        <label>Amount ($)</label>
                        <input type="number" class="funding-amount" min="0" step="1" value="2500000">
                    </div>
                    <div class="form-group" style="display: flex; align-items: flex-end;">
                        <button type="button" class="btn btn-danger remove-funding" style="padding: 0.5rem;">×</button>
                    </div>
                </div>
            </div>
            <button type="button" class="btn btn-secondary" onclick="addFunding()">+ Add Funding Source</button>
            
            <input type="hidden" id="dwelling_data" name="dwelling_data">
            <input type="hidden" id="funding_sources" name="funding_sources">
            
            <div class="mt-3">
                <button type="submit" class="btn btn-success">Save Project</button>
                <a href="/" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
    """
    
    scripts = """
    function addDwelling() {
        const container = document.getElementById('dwellings-container');
        const row = document.createElement('div');
        row.className = 'form-row dwelling-row';
        row.innerHTML = `
            <div class="form-group">
                <label>Type</label>
                <input type="text" class="dwelling-type" placeholder="e.g., 3x2" value="2x1">
            </div>
            <div class="form-group">
                <label>Count</label>
                <input type="number" class="dwelling-count" min="1" value="1">
            </div>
            <div class="form-group">
                <label>Bedrooms</label>
                <input type="number" class="dwelling-bedrooms" min="0" value="2">
            </div>
            <div class="form-group">
                <label>Bathrooms</label>
                <input type="number" class="dwelling-bathrooms" min="0" step="0.5" value="1">
            </div>
            <div class="form-group">
                <label>Area (sqm)</label>
                <input type="number" class="dwelling-area" min="20" value="90">
            </div>
            <div class="form-group" style="display: flex; align-items: flex-end;">
                <button type="button" class="btn btn-danger remove-dwelling" style="padding: 0.5rem;">×</button>
            </div>
        `;
        container.appendChild(row);
        updateRemoveButtons();
    }
    
    function updateRemoveButtons() {
        document.querySelectorAll('.remove-dwelling').forEach(btn => {
            btn.onclick = function() {
                const row = this.closest('.dwelling-row');
                if (document.querySelectorAll('.dwelling-row').length > 1) {
                    row.remove();
                }
            };
        });
        document.querySelectorAll('.remove-funding').forEach(btn => {
            btn.onclick = function() {
                const row = this.closest('.funding-row');
                if (document.querySelectorAll('.funding-row').length > 1) {
                    row.remove();
                }
            };
        });
    }
    updateRemoveButtons();
    
    function addFunding() {
        const container = document.getElementById('funding-container');
        const row = document.createElement('div');
        row.className = 'form-row funding-row';
        row.innerHTML = `
            <div class="form-group">
                <label>Source</label>
                <input type="text" class="funding-source" placeholder="e.g., Philanthropic" value="Philanthropic">
            </div>
            <div class="form-group">
                <label>Amount ($)</label>
                <input type="number" class="funding-amount" min="0" step="1" value="1000000">
            </div>
            <div class="form-group" style="display: flex; align-items: flex-end;">
                <button type="button" class="btn btn-danger remove-funding" style="padding: 0.5rem;">×</button>
            </div>
        `;
        container.appendChild(row);
        updateRemoveButtons();
    }
    
    document.getElementById('projectForm').addEventListener('submit', function(e) {
        const dwellings = [];
        document.querySelectorAll('.dwelling-row').forEach(row => {
            dwellings.push({
                type: row.querySelector('.dwelling-type').value || 'unknown',
                count: parseInt(row.querySelector('.dwelling-count').value) || 1,
                bedrooms: parseInt(row.querySelector('.dwelling-bedrooms').value) || 0,
                bathrooms: parseFloat(row.querySelector('.dwelling-bathrooms').value) || 0,
                area_sqm: parseFloat(row.querySelector('.dwelling-area').value) || 50,
                construction_type: 'standard'
            });
        });
        document.getElementById('dwelling_data').value = JSON.stringify(dwellings);
        
        const funding = [];
        document.querySelectorAll('.funding-row').forEach(row => {
            const source = row.querySelector('.funding-source').value;
            const amount = parseFloat(row.querySelector('.funding-amount').value);
            if (source && amount > 0) {
                funding.push({ source, amount });
            }
        });
        document.getElementById('funding_sources').value = JSON.stringify(funding);
    });
    """
    
    return HTMLResponse(content=get_base_html("New Project", content, scripts))

@app.get("/project/{project_name}", response_class=HTMLResponse)
async def view_project(request: Request, project_name: str):
    """View a single project with dashboard - Multi-Agent Version"""
    try:
        data = loader.load_project(project_name)
        
        # Run ALL agents using the orchestrator
        orchestrator = AgentOrchestrator(loader)
        all_results = orchestrator.run_all()
        
        # Get individual agent results
        cost_result = all_results.get("cost", {})
        planning_result = all_results.get("planning", {})
        env_result = all_results.get("environmental", {})
        traffic_result = all_results.get("traffic", {})
        urban_result = all_results.get("urban_design", {})
        
        # Extract data from each agent
        costs = cost_result.get("results", {}).get("cost_breakdown", {})
        funding = cost_result.get("results", {}).get("funding_analysis", {})
        cost_metrics = cost_result.get("results", {}).get("unit_metrics", {})
        cost_summary = cost_result.get("results", {}).get("project_summary", {})
        
        planning = planning_result.get("results", {}).get("planning_summary", {})
        approval = planning_result.get("results", {}).get("approval_requirements", {})
        
        env = env_result.get("results", {}).get("environmental_assessment", {})
        env_significance = env_result.get("results", {}).get("significance", {})
        
        traffic = traffic_result.get("results", {}).get("trip_generation", {})
        traffic_reqs = traffic_result.get("results", {}).get("traffic_requirements", {})
        
        urban = urban_result.get("results", {}).get("yield_analysis", {})
        density = urban_result.get("results", {}).get("density_analysis", {})
        
        total_cost = costs.get("total_cost")
        total_funding = funding.get("total_funding_available")
        funding_gap = funding.get("funding_gap")
# Doctrine A7: funding may be None (withheld). Feasibility is then
# UNDETERMINED - never fabricated as a verdict.
        if funding_gap is None:
            is_feasible = None
            feasibility_alert = "alert-info"
            feasibility_label = "\u2139 Feasibility Undetermined"
            feasibility_note = "Funding data is withheld (policy A7); feasibility cannot be assessed."
        elif funding_gap <= 0:
            is_feasible = True
            feasibility_alert = "alert-success"
            feasibility_label = "\u2705 Feasible"
            feasibility_note = "This project appears financially viable."
        else:
            is_feasible = False
            feasibility_alert = "alert-danger"
            feasibility_label = "\u274c Not Feasible"
            feasibility_note = f"Funding shortfall of ${funding_gap:,.2f}. Consider reducing scope or finding additional funding."
        
        # Get agent status
        agent_status = orchestrator.get_agent_status()
        
        # Build agent status badges
        status_badges = ""
        for agent, status in agent_status.items():
            status_class = "success" if status == "success" else "failed"
            emoji = "✅" if status == "success" else "❌"
            status_badges += f'<span class="agent-status {status_class}">{emoji} {agent.title()}</span> '
        
        # Determine if this is residential or commercial
        project_type = data["project"]["type"]
        is_commercial = project_type == "commercial"
        
        # Build dwellings table
        dwellings_html = ""
        if data.get("buildings", {}).get("homes"):
            for home in data["buildings"]["homes"]:
                dwellings_html += f"""
                <tr>
                    <td>{home.get('type', 'Unknown')}</td>
                    <td>{home.get('count', 0)}</td>
                    <td>{home.get('bedrooms', 0)}</td>
                    <td>{home.get('bathrooms', 0)}</td>
                    <td class="text-right">{home.get('area_sqm', 0)}</td>
                    <td class="text-right">{home.get('count', 0) * home.get('area_sqm', 0)}</td>
                </tr>
                """
        
        if data.get("buildings", {}).get("commercial"):
            for building in data["buildings"]["commercial"]:
                dwellings_html += f"""
                <tr>
                    <td>{building.get('name', 'Commercial')}</td>
                    <td>1</td>
                    <td>-</td>
                    <td>-</td>
                    <td class="text-right">{building.get('area_sqm', 0)}</td>
                    <td class="text-right">{building.get('area_sqm', 0)}</td>
                </tr>
                """
        
        if data.get("buildings", {}).get("dorms"):
            for dorm in data["buildings"]["dorms"]:
                dwellings_html += f"""
                <tr>
                    <td>Dorm ({dorm.get('rooms', 0)} rooms)</td>
                    <td>{dorm.get('count', 0)}</td>
                    <td>-</td>
                    <td>-</td>
                    <td class="text-right">{dorm.get('area_sqm', 0)}</td>
                    <td class="text-right">{dorm.get('count', 0) * dorm.get('area_sqm', 0)}</td>
                </tr>
                """
        
        if not dwellings_html:
            dwellings_html = '<tr><td colspan="6" class="text-muted">No buildings defined</td></tr>'
        
        # Build funding table
        funding_html = ""
        if data.get("funding", {}).get("sources"):
            for source in data["funding"]["sources"]:
                funding_html += f"""
                <tr>
                    <td>{source.get('source', 'Unknown')}</td>
                    <td class="text-right">${money(source.get('amount'))}</td>
                </tr>
                """
        
        # Build cost breakdown table
        cost_breakdown_html = f"""
        <tr><td>Planning</td><td class="text-right">{money(costs.get('planning_cost'))}</td><td class="text-right">{pct_share(costs.get('planning_cost'), total_cost)}%</td></tr>
        <tr><td>Infrastructure</td><td class="text-right">{money(costs.get('infrastructure_cost'))}</td><td class="text-right">{pct_share(costs.get('infrastructure_cost'), total_cost)}%</td></tr>
        <tr><td>Construction</td><td class="text-right">{money(costs.get('construction_cost'))}</td><td class="text-right">{pct_share(costs.get('construction_cost'), total_cost)}%</td></tr>
        <tr><td>Project Management</td><td class="text-right">{money(costs.get('management_cost'))}</td><td class="text-right">{pct_share(costs.get('management_cost'), total_cost)}%</td></tr>
        <tr><td>Contingency ({dash(costs.get('contingency_percent'))}%)</td><td class="text-right">{money(costs.get('contingency'))}</td><td class="text-right">{pct_share(costs.get('contingency'), total_cost)}%</td></tr>
        <tr style="font-weight:700;background:#f8f9fa;"><td>TOTAL</td><td class="text-right">{money(total_cost)}</td><td class="text-right">100%</td></tr>
        """
        
        # Determine building count label
        if is_commercial:
            building_label = "Commercial Buildings"
            count_label = "Total Buildings"
        else:
            building_label = "Dwellings"
            count_label = "Total Dwellings"
        
        # Get the appropriate cost per unit
        if is_commercial:
            cost_per_unit = money(cost_metrics.get('cost_per_building'))
        else:
            cost_per_unit = money(cost_metrics.get('cost_per_dwelling'))
        
        # Unit metrics grid
        unit_metrics_html = f"""
        <div class="grid">
            <div class="metric-card"><div class="label">{count_label}</div><div class="value">{dash(cost_summary.get('total_buildings'))}</div></div>
            <div class="metric-card"><div class="label">Cost per {building_label[:-1] if building_label.endswith('s') else building_label}</div><div class="value">{cost_per_unit}</div></div>
            <div class="metric-card"><div class="label">Total Building Area</div><div class="value">{qty(cost_summary.get('total_area_sqm'))} sqm</div></div>
            <div class="metric-card"><div class="label">Cost per sqm</div><div class="value">{money(cost_metrics.get('cost_per_sqm'))}</div></div>
        </div>
        """
        
        # Build planning section
        planning_html = f"""
        <div class="grid">
            <div class="metric-card">
                <div class="label">Zoning</div>
                <div class="value" style="font-size:1rem;">{planning.get('zoning', 'Unknown')}</div>
            </div>
            <div class="metric-card">
                <div class="label">Approval Pathway</div>
                <div class="value" style="font-size:1rem;">{approval.get('pathway', 'Unknown')}</div>
            </div>
            <div class="metric-card">
                <div class="label">Timeline</div>
                <div class="value" style="font-size:1rem;">{approval.get('estimated_timeline_months', 'N/A')} months</div>
            </div>
            <div class="metric-card">
                <div class="label">Rezoning Required</div>
                <div class="value" style="font-size:1rem;">{'Yes' if planning.get('rezoning_required', False) else 'No'}</div>
            </div>
        </div>
        <div style="margin-top:1rem;">
            <strong>Required Documentation:</strong>
            <ul>
                {"".join([f'<li>{doc}</li>' for doc in approval.get('required_documentation', [])])}
            </ul>
        </div>
        """
        
        # Build environmental section
        bal = env.get('bal_assessment', {})
        env_html = f"""
        <div class="grid">
            <div class="metric-card">
                <div class="label">BAL Rating</div>
                <div class="value" style="font-size:1.2rem;">{bal.get('rating', 'Unknown')}</div>
            </div>
            <div class="metric-card">
                <div class="label">Bushfire Risk</div>
                <div class="value" style="font-size:1rem;">{env.get('constraints', {}).get('bushfire_risk', 'Unknown')}</div>
            </div>
            <div class="metric-card">
                <div class="label">Heritage Present</div>
                <div class="value" style="font-size:1rem;">{'Yes' if env_significance.get('heritage_present', False) else 'No'}</div>
            </div>
            <div class="metric-card">
                <div class="label">Environmental Significance</div>
                <div class="value" style="font-size:1rem;">{env_significance.get('environmental_significance', 'Unknown')}</div>
            </div>
        </div>
        """
        
        # Build traffic section
        traffic_html = f"""
        <div class="grid">
            <div class="metric-card">
                <div class="label">Daily Trips</div>
                <div class="value">{traffic.get('daily_trips', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="label">AM Peak Trips</div>
                <div class="value">{traffic.get('am_peak_trips', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="label">PM Peak Trips</div>
                <div class="value">{traffic.get('pm_peak_trips', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="label">TIA Required</div>
                <div class="value" style="font-size:1rem;">{'Yes' if traffic_reqs.get('tia_required', False) else 'No'}</div>
            </div>
        </div>
        """
        
        # Build the complete content
        content = f"""
        <div class="flex">
            <h2>📊 {data['project']['name']}</h2>
            <div style="display:flex;gap:0.5rem;">
                <a href="/" class="btn btn-secondary">← All Projects</a>
                <button class="btn btn-primary" onclick="window.print()">🖨️ Print</button>
            </div>
        </div>
        
        <div class="alert {feasibility_alert}">
            <strong>{feasibility_label}</strong>
            {feasibility_note}
        </div>
        
        <div class="alert alert-info">
            <strong>🤖 Agents Run:</strong> {status_badges}
        </div>
        
        <!-- Financial Summary -->
        <div class="card">
            <h2>💰 Financial Summary</h2>
            <div class="grid">
                <div class="metric-card"><div class="label">Project Type</div><div class="value" style="font-size:1.2rem;">{data['project']['type'].replace('_', ' ').title()}</div></div>
                <div class="metric-card"><div class="label">Location</div><div class="value" style="font-size:1.2rem;">{data['project']['location'].title()}</div></div>
                <div class="metric-card"><div class="label">Site Area</div><div class="value">{data['project']['site_area_ha']} ha</div></div>
                <div class="metric-card"><div class="label">{count_label}</div><div class="value">{dash(cost_summary.get('total_buildings'))}</div></div>
                <div class="metric-card"><div class="label">Total Cost</div><div class="value">{money(total_cost)}</div></div>
                <div class="metric-card"><div class="label">Total Funding</div><div class="value">{money(total_funding)}</div></div>
                <div class="metric-card"><div class="label">Funding Gap</div><div class="value {'negative' if isinstance(funding_gap, (int, float)) and funding_gap > 0 else 'positive'}">{money(funding_gap)}</div></div>
                <div class="metric-card"><div class="label">Building Description</div><div class="value" style="font-size:1rem;">{cost_summary.get('building_description', 'N/A')}</div></div>
            </div>
        </div>
        
        <!-- Cost Breakdown -->
        <div class="card">
            <h2>📊 Cost Breakdown</h2>
            <table class="table">
                <thead><tr><th>Phase</th><th class="text-right">Cost</th><th class="text-right">% of Total</th></tr></thead>
                <tbody>{cost_breakdown_html}</tbody>
            </table>
        </div>
        
        <!-- Funding Sources -->
        <div class="card">
            <h2>💵 Funding Sources</h2>
            <table class="table">
                <thead><tr><th>Source</th><th class="text-right">Amount</th></tr></thead>
                <tbody>{funding_html if funding_html else '<tr><td colspan="2" class="text-muted">No funding sources listed</td></tr>'}</tbody>
            </table>
        </div>
        
        <!-- Unit Metrics -->
        <div class="card">
            <h2>🏠 Unit Metrics</h2>
            {unit_metrics_html}
        </div>
        
        <!-- Planning -->
        <div class="card">
            <h2>📋 Planning Analysis</h2>
            {planning_html}
        </div>
        
        <!-- Environmental -->
        <div class="card">
            <h2>🌿 Environmental Assessment</h2>
            {env_html}
        </div>
        
        <!-- Traffic -->
        <div class="card">
            <h2>🚗 Traffic Analysis</h2>
            {traffic_html}
        </div>
        
        <!-- Building Details -->
        <div class="card">
            <h2>🏗️ {building_label} Details</h2>
            <table class="table">
                <thead><tr><th>Type</th><th>Count</th><th>Bedrooms</th><th>Bathrooms</th><th class="text-right">Area (sqm)</th><th class="text-right">Total Area</th></tr></thead>
                <tbody>{dwellings_html}</tbody>
            </table>
        </div>
        """
        
        # Add infrastructure if present
        if data.get("infrastructure"):
            infra_html = ""
            if data["infrastructure"].get("water"):
                infra_html += f"""
                <div class="metric-card">
                    <div class="label">Water</div>
                    <div class="value" style="font-size:1rem;">{data['infrastructure']['water'].get('existing', 'N/A').title()}</div>
                    <div class="text-muted" style="font-size:0.85rem;">Crossovers: {data['infrastructure']['water'].get('crossovers', 0)} | Cost: {money(data['infrastructure']['water'].get('cost_per'))}/ea</div>
                </div>
                """
            if data["infrastructure"].get("power"):
                infra_html += f"""
                <div class="metric-card">
                    <div class="label">Power</div>
                    <div class="value" style="font-size:1rem;">{data['infrastructure']['power'].get('existing', 'N/A').title()}</div>
                    <div class="text-muted" style="font-size:0.85rem;">Connections: {data['infrastructure']['power'].get('connections', 0)} | Cost: {money(data['infrastructure']['power'].get('cost_per'))}/ea</div>
                </div>
                """
            if data["infrastructure"].get("sewer"):
                infra_html += f"""
                <div class="metric-card">
                    <div class="label">Sewer</div>
                    <div class="value" style="font-size:1rem;">{data['infrastructure']['sewer'].get('type', 'N/A').title()}</div>
                    <div class="text-muted" style="font-size:0.85rem;">Units: {data['infrastructure']['sewer'].get('units', 0)} | Cost: {money(data['infrastructure']['sewer'].get('cost_per'))}/ea</div>
                </div>
                """
            if data["infrastructure"].get("roads"):
                infra_html += f"""
                <div class="metric-card">
                    <div class="label">Roads</div>
                    <div class="value" style="font-size:1rem;">{data['infrastructure']['roads'].get('existing', 'N/A').title()}</div>
                    <div class="text-muted" style="font-size:0.85rem;">Upgrade Needed: {data['infrastructure']['roads'].get('upgrade_needed', False)} | Cost: {money(data['infrastructure']['roads'].get('cost'))}</div>
                </div>
                """
            if infra_html:
                content += f"""
                <div class="card">
                    <h2>🔧 Infrastructure</h2>
                    <div class="grid">{infra_html}</div>
                </div>
                """
        
        # Add site description if present
        if data["project"].get("site_description"):
            content += f"""
            <div class="card">
                <h2>📝 Site Description</h2>
                <p>{data['project']['site_description']}</p>
            </div>
            """
        
        # Add lease details if present
        if data["project"].get("lease_terms"):
            lease = data["project"]["lease_terms"]
            content += f"""
            <div class="card">
                <h2>📄 Lease Details</h2>
                <div class="grid">
                    <div class="metric-card"><div class="label">Tenure</div><div class="value" style="font-size:1rem;">{data['project'].get('land_tenure', 'N/A').title()}</div></div>
                    <div class="metric-card"><div class="label">Years Remaining</div><div class="value" style="font-size:1rem;">{lease.get('years_remaining', 'N/A')} years</div></div>
                    <div class="metric-card"><div class="label">Annual Rent</div><div class="value" style="font-size:1rem;">${money(lease.get('annual_rent'))}</div></div>
                </div>
            </div>
            """
        
        content += f"""
        <div class="card text-center">
            <h2>📤 Export Data</h2>
            <button class="btn btn-primary" onclick="exportJSON()">Download All Agent Results</button>
        </div>
        """
        
        scripts = f"""
        function exportJSON() {{
            fetch('/api/project/{project_name}/analysis')
                .then(response => response.json())
                .then(data => {{
                    const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '{project_name}_analysis.json';
                    a.click();
                    URL.revokeObjectURL(url);
                }});
        }}
        """
        
        return HTMLResponse(content=get_base_html(f"Dashboard - {data['project']['name']}", content, scripts))
        
    except Exception as e:
        return HTMLResponse(content=get_base_html("Error", f'<div class="alert alert-danger">Error loading project: {str(e)}</div>'))

# ============ API ROUTES ============

@app.post("/api/project/upload")
async def upload_project_file(file: UploadFile = File(...)):
    """Upload a project JSON file"""
    try:
        content = await file.read()
        data = json.loads(content)
        
        validator = ProjectSchemaValidator()
        is_valid, errors = validator.validate(data)
        
        if not is_valid:
            return JSONResponse({
                "status": "error",
                "errors": errors
            }, status_code=400)
        
        project_name = data["project"]["name"].replace(" ", "_").lower()
        loader.save_project(data, project_name)
        
        return JSONResponse({
            "status": "success",
            "project_name": project_name,
            "message": f"Project '{project_name}' uploaded successfully"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=400)

@app.get("/api/projects/list")
async def list_projects():
    """List all projects"""
    projects = loader.list_projects()
    return JSONResponse(projects)

@app.delete("/api/project/{project_name}")
async def delete_project(project_name: str):
    """Delete a project"""
    try:
        success = loader.delete_project(project_name)
        return JSONResponse({
            "status": "success",
            "message": f"Project '{project_name}' deleted"
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/project/save")
async def save_project(
    project_name: str = Form(...),
    project_type: str = Form(...),
    location: str = Form(...),
    site_area_ha: float = Form(...),
    land_tenure: str = Form(...),
    land_cost: float = Form(0),
    dwelling_data: str = Form(...),
    planning_cost: float = Form(0),
    infrastructure_cost: float = Form(0),
    construction_cost: float = Form(0),
    management_cost: float = Form(0),
    contingency_percent: float = Form(10),
    funding_sources: str = Form(...),
    description: Optional[str] = Form(None)
):
    """Save a new project from form data"""
    try:
        dwellings = json.loads(dwelling_data)
        funding = json.loads(funding_sources)
        
        project_data = {
            "project": {
                "name": project_name,
                "type": project_type,
                "location": location,
                "site_area_ha": site_area_ha,
                "land_tenure": land_tenure,
                "land_cost": land_cost,
                "site_description": description or ""
            },
            "buildings": {
                "homes": dwellings
            },
            "phases": {
                "planning": {"cost": planning_cost},
                "infrastructure": {"cost": infrastructure_cost},
                "construction": {"cost": construction_cost},
                "project_management": {"cost": management_cost},
                "contingency_percent": contingency_percent
            },
            "funding": {
                "model": "mixed",
                "sources": funding
            }
        }
        
        loader.save_project(project_data, project_name)
        return RedirectResponse(f"/project/{project_name}", status_code=303)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/project/{project_name}/analysis")
async def get_project_analysis(project_name: str):
    """API endpoint to get project analysis from ALL agents as JSON"""
    try:
        loader.load_project(project_name)
        orchestrator = AgentOrchestrator(loader)
        results = orchestrator.run_all()
        return JSONResponse(results)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/project/{project_name}/data")
async def get_project_data(project_name: str):
    """API endpoint to get project data as JSON"""
    try:
        data = loader.load_project(project_name)
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/project/{project_name}/summary")
async def get_project_summary(project_name: str):
    """API endpoint to get a concise project summary"""
    try:
        loader.load_project(project_name)
        orchestrator = AgentOrchestrator(loader)
        results = orchestrator.run_all()
        
        # Extract key metrics
        cost_result = results.get("cost", {}).get("results", {})
        planning_result = results.get("planning", {}).get("results", {})
        env_result = results.get("environmental", {}).get("results", {})
        traffic_result = results.get("traffic", {}).get("results", {})
        
        summary = {
            "project_name": project_name,
            "feasibility": {
                "total_cost": cost_result.get("cost_breakdown", {}).get("total_cost", 0),
                "funding_gap": cost_result.get("funding_analysis", {}).get("funding_gap", 0),
                "is_feasible": (None if cost_result.get("funding_analysis", {}).get("funding_gap") is None else cost_result.get("funding_analysis", {}).get("funding_gap", 0) <= 0)
            },
            "planning": {
                "pathway": planning_result.get("approval_requirements", {}).get("pathway", "Unknown"),
                "timeline_months": planning_result.get("approval_requirements", {}).get("estimated_timeline_months", 0)
            },
            "environment": {
                "bal_rating": env_result.get("environmental_assessment", {}).get("bal_assessment", {}).get("rating", "Unknown"),
                "heritage_present": env_result.get("significance", {}).get("heritage_present", False)
            },
            "traffic": {
                "daily_trips": traffic_result.get("trip_generation", {}).get("daily_trips", 0)
            }
        }
        return JSONResponse(summary)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
