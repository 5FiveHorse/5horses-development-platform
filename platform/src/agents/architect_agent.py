"""
ArchitectAgent - Architectural schematics, drawings, and renderings
For 5Horses Property Development Platform - Western Australia

Migrated to the Phase 1 Foundation pattern:
- Inherits BaseAgent, reads exclusively from project_data.json via get_project_data()
- No hardcoded per-project values; new projects require no code changes
- Produces 2D concept renderings (Stable Diffusion/Replicate, optional) AND
  3D geometry + renders (Blender MCP bridge, optional)

Both are optional integrations: if replicate/PIL aren't installed, or Blender
isn't running, ArchitectAgent still returns full design output - it just
skips the corresponding rendering step and says so in the results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import os

from src.agents.base_agent import BaseAgent

try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False

try:
    from src.agents.blender_bridge import get_blender_bridge
    BLENDER_BRIDGE_AVAILABLE = True
except ImportError:
    BLENDER_BRIDGE_AVAILABLE = False


class BuildingType(Enum):
    SINGLE_STOREY = "Single Storey House"
    DOUBLE_STOREY = "Double Storey House"
    TOWNHOUSE = "Townhouse"
    APARTMENT = "Apartment Building"
    MIXED_USE = "Mixed Use Development"
    COMMUNITY = "Community Centre"
    GALLERY = "Art Gallery"
    SCHOOL = "Vocational School"
    OFFICE = "Office Building"
    RETAIL = "Retail Building"


class DesignStyle(Enum):
    CONTEMPORARY = "Contemporary - Clean lines, large windows"
    HAMPTON = "Hampton - Weatherboard, pitched roof"
    FEDERATION = "Federation - Ornate details, verandahs"
    MODERN_FARMHOUSE = "Modern Farmhouse - Rural aesthetic"
    COASTAL = "Coastal - Light colours, relaxed design"
    CULTURAL = "Indigenous Cultural - Aboriginal design elements"
    SUSTAINABLE = "Sustainable - Passive solar, green roof"


class DrawingType(Enum):
    SITE_PLAN = "Site Plan (1:500)"
    FLOOR_PLAN = "Floor Plan (1:100)"
    ELEVATION = "Elevations (1:100)"
    SECTION = "Building Sections (1:100)"
    DETAIL = "Construction Details (1:20)"
    RENDERING = "3D Renderings - External"
    INTERIOR = "Interior Renderings"
    LANDSCAPE = "Landscape Plan"
    AERIAL = "Aerial Perspective"
    STREETSCAPE = "Streetscape View"


@dataclass
class ArchitecturalDrawing:
    drawing_id: str
    drawing_type: DrawingType
    title: str
    scale: str
    status: str
    revision: str = "00"
    file_reference: str = ""
    rendering_url: str = ""


@dataclass
class FloorPlan:
    name: str
    bedrooms: int
    bathrooms: float
    area_sqm: float
    count: int
    features: List[str]


@dataclass
class BuildingDesign:
    source_type: str          # "home" | "commercial" | "dorm"
    schema_type: str          # raw value from project_data.json, e.g. "3x2" or "gallery"
    building_type: BuildingType
    design_style: DesignStyle
    floor_plans: List[FloorPlan]
    external_finishes: List[str]
    sustainability_features: List[str]
    cultural_elements: List[str] = field(default_factory=list)
    blender_render_path: Optional[str] = None
    concept_render_path: Optional[str] = None


# --- Schema -> design vocabulary mappings -----------------------------------
# The schema's buildings.homes[].type field is a bed/bath shorthand (e.g. "3x2"),
# not a building typology, so home building_type is inferred from construction
# context rather than parsed from that string.
HOME_CONSTRUCTION_TO_BUILDING_TYPE = {
    "standard": BuildingType.SINGLE_STOREY,
    "modular": BuildingType.TOWNHOUSE,
}

# buildings.commercial[].type strings -> BuildingType
COMMERCIAL_TYPE_TO_BUILDING_TYPE = {
    "gallery": BuildingType.GALLERY,
    "office": BuildingType.OFFICE,
    "education": BuildingType.SCHOOL,
    "retail": BuildingType.RETAIL,
    "community": BuildingType.COMMUNITY,
}

# project.type -> default DesignStyle when no explicit override is given
PROJECT_TYPE_TO_DESIGN_STYLE = {
    "community_housing": DesignStyle.CULTURAL,
    "social_housing": DesignStyle.CULTURAL,
    "commercial": DesignStyle.CONTEMPORARY,
    "traditional": DesignStyle.HAMPTON,
}

FINISHES_MAP = {
    DesignStyle.CONTEMPORARY: ["Rendered blockwork", "Timber battens", "Aluminium windows", "Flat roof"],
    DesignStyle.HAMPTON: ["Weatherboard cladding", "Gable roof", "Timber windows", "Wraparound verandah"],
    DesignStyle.MODERN_FARMHOUSE: ["Corrugated iron roof", "Timber posts", "Stone accents", "Pitched roof"],
    DesignStyle.COASTAL: ["Weatherboard", "Corrugated iron", "Large glazing", "Outdoor decks"],
    DesignStyle.FEDERATION: ["Brickwork", "Ornamental timber", "Leadlight windows", "Decorative gables"],
    DesignStyle.CULTURAL: ["Earthy render", "Timber screens", "Cultural artwork", "Shaded outdoor spaces"],
    DesignStyle.SUSTAINABLE: ["Recycled materials", "Green roof", "Passive design", "Solar panels"],
}

SUSTAINABILITY_FEATURES = [
    "7-star energy rating (above NCC)",
    "Solar passive orientation",
    "LED lighting throughout",
    "Water-efficient fixtures (WELS 5-star)",
    "Rainwater tank (5000L)",
    "Native landscaping (waterwise)",
    "Solar PV system (6.6kW)",
    "Battery-ready electrical",
]

# Cultural design elements by location. Keys are normalized (lowercase,
# spaces -> underscores) at lookup time so they match project.location
# values from the schema regardless of how they were originally typed here.
CULTURAL_ELEMENTS = {
    "gnowangerup": [
        "Aboriginal art murals on key buildings",
        "Meeting place / yarning circle",
        "Interpretive signage in Noongar language",
        "Native bush tucker garden",
        "Cultural burning practices for land management",
    ],
    "mount_barker": [
        "Welcome to Country artwork at entrance",
        "Cultural interpretation centre",
        "Traditional shelter structures (Mia-mia)",
        "Art gallery featuring local Aboriginal artists",
    ],
    "default": [
        "Indigenous art integration",
        "Community gathering spaces",
        "Connection to Country design principles",
    ],
}


def _normalize_location_key(location: str) -> str:
    """'Mount Barker' / 'mount_barker' / 'MOUNT BARKER' all normalize the same way."""
    return location.strip().lower().replace(" ", "_")


class ArchitectAgent(BaseAgent):
    """
    Design & renderings agent.

    Reads buildings.homes / buildings.commercial / buildings.dorms from
    project_data.json and produces:
      - BuildingDesign objects (floor plans, finishes, cultural elements)
      - A DA-ready drawing register
      - Optional 2D concept renderings (Stable Diffusion via Replicate)
      - Optional 3D geometry + renders (Blender MCP bridge)
    """

    def __init__(self, project_loader=None, enable_2d_rendering: bool = True,
                 enable_3d_rendering: bool = True):
        super().__init__(project_loader)
        self.enable_2d_rendering = enable_2d_rendering and REPLICATE_AVAILABLE
        self.enable_3d_rendering = enable_3d_rendering and BLENDER_BRIDGE_AVAILABLE
        self.rendering_dir = "outputs/renderings"
        os.makedirs(self.rendering_dir, exist_ok=True)
        self.drawings: List[ArchitecturalDrawing] = []
        self.designs: List[BuildingDesign] = []

    # ------------------------------------------------------------------
    # BaseAgent overrides
    # ------------------------------------------------------------------

    def get_required_inputs(self) -> list:
        return ["project.type", "project.location", "buildings"]

    def validate_inputs(self) -> bool:
        ok = True
        for path in self.get_required_inputs():
            if self.get_project_data(path) is None:
                self.logger.warning(f"Missing required input: {path}")
                ok = False
        homes = self.get_project_data("buildings.homes") or []
        commercial = self.get_project_data("buildings.commercial") or []
        dorms = self.get_project_data("buildings.dorms") or []
        if not (homes or commercial or dorms):
            self.logger.warning("buildings has no homes, commercial, or dorms entries")
            ok = False
        return ok

    def process(self) -> Dict[str, Any]:
        self.logger.info("Starting architectural design generation...")
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for ArchitectAgent")

        self.designs = []
        self.drawings = []

        location = self.get_project_data("project.location") or "default"
        project_type = self.get_project_data("project.type") or "traditional"
        project_name = self.get_project_data("project.name") or "Unnamed Project"

        cultural = self._get_cultural_elements(location)
        design_style = self._infer_design_style(project_type)

        homes = self.get_project_data("buildings.homes") or []
        commercial = self.get_project_data("buildings.commercial") or []
        dorms = self.get_project_data("buildings.dorms") or []

        for home in homes:
            self.designs.append(self._build_home_design(home, design_style, cultural))
        for comm in commercial:
            self.designs.append(self._build_commercial_design(comm, design_style, cultural))
        for dorm in dorms:
            self.designs.append(self._build_dorm_design(dorm, design_style, cultural))

        # Drawing register
        is_cultural_project = cultural is not CULTURAL_ELEMENTS["default"]
        register_context = f"{project_type}{' - Aboriginal cultural' if is_cultural_project else ''}"
        self._populate_drawing_register(register_context)

        # Optional renderings
        render_summary = self._generate_renderings(project_name)

        results = {
            "project_name": project_name,
            "location": location,
            "design_style": design_style.value,
            "cultural_elements": cultural,
            "designs": [self._design_to_dict(d) for d in self.designs],
            "drawing_register": [self._drawing_to_dict(d) for d in self.drawings],
            "rendering_summary": render_summary,
        }
        self.logger.info(
            f"Design generation complete: {len(self.designs)} building designs, "
            f"{len(self.drawings)} drawings."
        )
        return self.format_output(results)

    # ------------------------------------------------------------------
    # Design construction
    # ------------------------------------------------------------------

    def _get_cultural_elements(self, location: str) -> List[str]:
        key = _normalize_location_key(location)
        return CULTURAL_ELEMENTS.get(key, CULTURAL_ELEMENTS["default"])

    def _infer_design_style(self, project_type: str) -> DesignStyle:
        override = self.get_project_data("project.design_style")
        if override:
            try:
                return DesignStyle[override.upper()]
            except KeyError:
                self.logger.warning(f"Unknown design_style override '{override}', using inferred default")
        return PROJECT_TYPE_TO_DESIGN_STYLE.get(project_type, DesignStyle.CONTEMPORARY)

    def _build_home_design(self, home: Dict[str, Any], design_style: DesignStyle,
                            cultural: List[str]) -> BuildingDesign:
        construction_type = home.get("construction_type", "standard")
        building_type = HOME_CONSTRUCTION_TO_BUILDING_TYPE.get(construction_type, BuildingType.SINGLE_STOREY)

        floor_plan = FloorPlan(
            name=f"{home.get('type', 'Home')} ({construction_type})",
            bedrooms=home.get("bedrooms", 0),
            bathrooms=home.get("bathrooms", 0),
            area_sqm=home.get("area_sqm", 0),
            count=home.get("count", 1),
            features=self._default_home_features(home),
        )

        return BuildingDesign(
            source_type="home",
            schema_type=home.get("type", "unknown"),
            building_type=building_type,
            design_style=design_style,
            floor_plans=[floor_plan],
            external_finishes=FINISHES_MAP.get(design_style, ["Standard finishes"]),
            sustainability_features=SUSTAINABILITY_FEATURES,
            cultural_elements=cultural,
        )

    def _build_commercial_design(self, comm: Dict[str, Any], design_style: DesignStyle,
                                  cultural: List[str]) -> BuildingDesign:
        schema_type = comm.get("type", "office")
        building_type = COMMERCIAL_TYPE_TO_BUILDING_TYPE.get(schema_type, BuildingType.MIXED_USE)

        floor_plan = FloorPlan(
            name=comm.get("name", "Commercial Building"),
            bedrooms=0,
            bathrooms=2,
            area_sqm=comm.get("area_sqm", 0),
            count=1,
            features=self._default_commercial_features(schema_type),
        )

        return BuildingDesign(
            source_type="commercial",
            schema_type=schema_type,
            building_type=building_type,
            design_style=design_style,
            floor_plans=[floor_plan],
            external_finishes=FINISHES_MAP.get(design_style, ["Standard finishes"]),
            sustainability_features=SUSTAINABILITY_FEATURES,
            cultural_elements=cultural,
        )

    def _build_dorm_design(self, dorm: Dict[str, Any], design_style: DesignStyle,
                            cultural: List[str]) -> BuildingDesign:
        construction = dorm.get("construction", "standard")
        building_type = HOME_CONSTRUCTION_TO_BUILDING_TYPE.get(construction, BuildingType.TOWNHOUSE)

        floor_plan = FloorPlan(
            name=f"Dormitory ({dorm.get('rooms', 0)} rooms, {construction})",
            bedrooms=dorm.get("rooms", 0),
            bathrooms=max(1, dorm.get("rooms", 0) // 3),
            area_sqm=dorm.get("area_sqm", 0),
            count=dorm.get("count", 1),
            features=["Shared living area", "Individual rooms", "Communal kitchen"],
        )

        return BuildingDesign(
            source_type="dorm",
            schema_type="dorm",
            building_type=building_type,
            design_style=design_style,
            floor_plans=[floor_plan],
            external_finishes=FINISHES_MAP.get(design_style, ["Standard finishes"]),
            sustainability_features=SUSTAINABILITY_FEATURES,
            cultural_elements=cultural,
        )

    def _default_home_features(self, home: Dict[str, Any]) -> List[str]:
        bedrooms = home.get("bedrooms", 0)
        features = ["Open plan living", "Alfresco"]
        if bedrooms >= 3:
            features += ["Walk-in pantry", "Walk-in robe"]
        if bedrooms >= 4:
            features += ["Theatre room", "Study nook"]
        return features

    def _default_commercial_features(self, schema_type: str) -> List[str]:
        return {
            "gallery": ["Exhibition halls", "Retail space", "Storage", "Workshop area", "Cafe"],
            "office": ["Open plan offices", "Meeting rooms", "Kitchenette", "Reception"],
            "education": ["Classrooms", "Workshop space", "Admin offices", "Student amenities"],
            "retail": ["Shopfront", "Storage", "Customer amenities"],
            "community": ["Multi-purpose hall", "Meeting rooms", "Commercial kitchen"],
        }.get(schema_type, ["Standard commercial fitout"])

    # ------------------------------------------------------------------
    # Drawing register
    # ------------------------------------------------------------------

    def _populate_drawing_register(self, project_type_context: str) -> None:
        standard_drawings = [
            (DrawingType.SITE_PLAN, "Site Analysis Plan", "1:500"),
            (DrawingType.SITE_PLAN, "Concept Masterplan", "1:500"),
            (DrawingType.FLOOR_PLAN, "Typical Floor Plans", "1:100"),
            (DrawingType.ELEVATION, "Typical Elevations", "1:100"),
            (DrawingType.RENDERING, "3D Massing Model", "N/A"),
            (DrawingType.STREETSCAPE, "Streetscape Elevations", "1:200"),
            (DrawingType.AERIAL, "Indicative Renderings", "N/A"),
        ]
        if "Aboriginal cultural" in project_type_context:
            standard_drawings += [
                (DrawingType.SITE_PLAN, "Cultural Interpretation Plan", "1:500"),
                (DrawingType.DETAIL, "Yarning Circle Design", "1:100"),
                (DrawingType.LANDSCAPE, "Native Bush Tucker Garden", "1:200"),
            ]
        for drawing_type, title, scale in standard_drawings:
            self.drawings.append(ArchitecturalDrawing(
                drawing_id=f"DRG-{len(self.drawings)+1:04d}",
                drawing_type=drawing_type,
                title=title,
                scale=scale,
                status="Draft",
            ))

    # ------------------------------------------------------------------
    # Renderings (both optional, both independently toggleable)
    # ------------------------------------------------------------------

    def _generate_renderings(self, project_name: str) -> Dict[str, Any]:
        summary = {
            "2d_concept_renderings": {"enabled": self.enable_2d_rendering, "generated": 0},
            "3d_blender_models": {"enabled": self.enable_3d_rendering, "generated": 0, "errors": []},
        }

        if not self.enable_2d_rendering:
            summary["2d_concept_renderings"]["reason"] = (
                "replicate not installed" if not REPLICATE_AVAILABLE else "disabled"
            )
        if not self.enable_3d_rendering:
            summary["3d_blender_models"]["reason"] = (
                "blender_bridge module not available" if not BLENDER_BRIDGE_AVAILABLE else "disabled"
            )

        if self.enable_3d_rendering:
            bridge = get_blender_bridge()
            for design in self.designs:
                if design.source_type != "home":
                    continue  # Blender bridge currently only models houses
                for fp in design.floor_plans:
                    result = bridge.create_house(
                        home_type=fp.name,
                        bedrooms=fp.bedrooms,
                        bathrooms=fp.bathrooms,
                        area_sqm=fp.area_sqm,
                    )
                    if result.get("status") == "success":
                        summary["3d_blender_models"]["generated"] += 1
                    else:
                        summary["3d_blender_models"]["errors"].append(
                            f"{fp.name}: {result.get('message', 'unknown error')}"
                        )

        return summary

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def _design_to_dict(self, d: BuildingDesign) -> Dict[str, Any]:
        return {
            "source_type": d.source_type,
            "schema_type": d.schema_type,
            "building_type": d.building_type.value,
            "design_style": d.design_style.value,
            "floor_plans": [
                {
                    "name": fp.name, "bedrooms": fp.bedrooms, "bathrooms": fp.bathrooms,
                    "area_sqm": fp.area_sqm, "count": fp.count, "features": fp.features,
                }
                for fp in d.floor_plans
            ],
            "external_finishes": d.external_finishes,
            "sustainability_features": d.sustainability_features,
            "cultural_elements": d.cultural_elements,
        }

    def _drawing_to_dict(self, dr: ArchitecturalDrawing) -> Dict[str, Any]:
        return {
            "drawing_id": dr.drawing_id, "type": dr.drawing_type.value,
            "title": dr.title, "scale": dr.scale, "status": dr.status,
        }
