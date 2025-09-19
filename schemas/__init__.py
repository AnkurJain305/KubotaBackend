# Core schemas
from .user import UserBase, UserCreate, UserUpdate, UserOut, UserWithRelations
from .machine import MachineBase, MachineCreate, MachineUpdate, MachineOut, MachineWithOwner
from .ticket import TicketBase, TicketCreate, TicketUpdate, TicketOut, TicketWithRelations

# Job management schemas
from .job import JobBase, JobCreate, JobUpdate, JobOut, JobWithParts, JobStatus
from .job_part import JobPartBase, JobPartCreate, JobPartUpdate, JobPartOut, JobPartWithDetails

# Parts and inventory schemas
from .part import (
    PartsInventoryBase, PartsInventoryCreate, PartsInventoryUpdate, PartsInventoryOut,
    PartsRequestBase, PartsRequestCreate, PartsRequestUpdate, PartsRequestOut
)

# Support schemas
from .cause import CauseBase, CauseCreate, CauseUpdate, CauseOut
from .notification import (
    NotificationBase, NotificationCreate, NotificationUpdate, NotificationOut,
    # SystemNotificationBase, SystemNotificationCreate, SystemNotificationOut
)

# AI workflow schemas
from .inventory import (
    TicketProcessingRequest, TicketProcessingResponse,
    RepairWorkflowRequest, RepairWorkflowResponse,
    UserFeedbackBase, UserFeedbackCreate, UserFeedbackOut
)

from .ai_schema import (
    AIRecommendationRequest, AIRecommendationResponse, 
    SimilaritySearchRequest, AISystemStatus , SimilarCase ,PartRecommendation 
)


__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserOut", "UserWithRelations",

    # Machine schemas  
    "MachineBase", "MachineCreate", "MachineUpdate", "MachineOut", "MachineWithOwner",

    # Ticket schemas
    "TicketBase", "TicketCreate", "TicketUpdate", "TicketOut", "TicketWithRelations",

    # Job schemas
    "JobBase", "JobCreate", "JobUpdate", "JobOut", "JobWithParts", "JobStatus",
    "JobPartBase", "JobPartCreate", "JobPartUpdate", "JobPartOut", "JobPartWithDetails",

    # Parts schemas
    "PartsInventoryBase", "PartsInventoryCreate", "PartsInventoryUpdate", "PartsInventoryOut",
    "PartsRequestBase", "PartsRequestCreate", "PartsRequestUpdate", "PartsRequestOut",

    # Support schemas
    "CauseBase", "CauseCreate", "CauseUpdate", "CauseOut",
    "NotificationBase", "NotificationCreate", "NotificationUpdate", "NotificationOut",
    # "SystemNotificationBase", "SystemNotificationCreate", "SystemNotificationOut",

    # AI workflow schemas
    "TicketProcessingRequest", "TicketProcessingResponse",
    "RepairWorkflowRequest", "RepairWorkflowResponse",
    "UserFeedbackBase", "UserFeedbackCreate", "UserFeedbackOut",

    # AI schemas
    "AIRecommendationRequest", "AIRecommendationResponse",
    "SimilaritySearchRequest", "AISystemStatus" , "SimilarCase" , "PartRecommendation"
]
