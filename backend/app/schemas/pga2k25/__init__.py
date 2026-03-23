"""PGA TOUR 2K25 Pydantic schemas — golf intelligence data contracts."""

from app.schemas.pga2k25.course import (
    CourseAnalysis,
    CourseAnalysisRequest,
    HazardRisk,
    HoleStrategy,
    LineEV,
    ShotPlan,
)
from app.schemas.pga2k25.swing import (
    ClubMissProfile,
    PressureDrift,
    SwingDiagnosis,
    SwingDiagnosisRequest,
    SwingFault,
    SwingSystem,
)
from app.schemas.pga2k25.green import (
    GreenRead,
    GreenReadRequest,
    PaceControl,
    PressurePuttingMode,
    PuttAnalysis,
    ThreePuttRisk,
)
from app.schemas.pga2k25.wind import (
    CarryTotalSplit,
    TrajectoryControl,
    WindAdjustedSelection,
    WindCondition,
    WindSelectionRequest,
)
from app.schemas.pga2k25.dispersion import (
    ClubDispersion,
    DispersionMap,
    DispersionMapRequest,
    MissPattern,
    SessionShot,
)
from app.schemas.pga2k25.ranked import (
    RankedEnvironment,
    RankedTrackingRequest,
    SocietyPrep,
    SocietyPrepRequest,
    TourReport,
)

__all__ = [
    # Course
    "CourseAnalysis",
    "CourseAnalysisRequest",
    "HazardRisk",
    "HoleStrategy",
    "LineEV",
    "ShotPlan",
    # Swing
    "ClubMissProfile",
    "PressureDrift",
    "SwingDiagnosis",
    "SwingDiagnosisRequest",
    "SwingFault",
    "SwingSystem",
    # Green
    "GreenRead",
    "GreenReadRequest",
    "PaceControl",
    "PressurePuttingMode",
    "PuttAnalysis",
    "ThreePuttRisk",
    # Wind
    "CarryTotalSplit",
    "TrajectoryControl",
    "WindAdjustedSelection",
    "WindCondition",
    "WindSelectionRequest",
    # Dispersion
    "ClubDispersion",
    "DispersionMap",
    "DispersionMapRequest",
    "MissPattern",
    "SessionShot",
    # Ranked
    "RankedEnvironment",
    "RankedTrackingRequest",
    "SocietyPrep",
    "SocietyPrepRequest",
    "TourReport",
]
