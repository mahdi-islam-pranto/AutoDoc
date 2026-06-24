from typing import TypedDict, Annotated, Any
from enum import Enum
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# booking state
# We track the user's progress through the booking funnel and stages with this enum.
class BookingStage(str, Enum):
    """
    Tracks exactly where the user is in the booking funnel.
    The supervisor and booking agent both use this to decide what to do next.
    """

    IDLE               = "idle"                # no active booking in progress
    SYMPTOM_COLLECTION = "symptom_collection"  # user described symptoms
    DOCTOR_SELECTION   = "doctor_selection"    # user chose or was shown a doctor
    SLOT_SELECTION     = "slot_selection"      # showing/picking time slots
    CONFIRMING         = "confirming"          # collecting name/phone, final confirm
    BOOKED             = "booked"              # appointment confirmed
    CANCELLING         = "cancelling"          # cancel flow in progress
    

# chat conversation state
class ConversationState(BaseModel):

    """
    The full state of one conversation. LangGraph passes this between every node.
    Each node receives it, does its work, and returns a dict of fields to update.
    LangGraph merges those updates back into the state automatically.
    """
    
    # messages is a special field that gets merged (not replaced) when returned from a node.
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    
    # Which agent the supervisor decided to route to
    next_agent: str = "supervisor"
    
    # Where in the booking funnel we are
    booking_stage: BookingStage = BookingStage.IDLE
    
    # Collected during the conversation
    symptoms: list[str] = Field(default_factory=list)
    selected_doctor_id: str | None = None
    selected_doctor_name: str | None = None
    selected_slot: str | None = None
    patient_name: str | None = None
    patient_phone: str | None = None
    confirmation_id: str | None = None
    doctor_specialization: str | None = None
    
    # Which channel this came from (whatsapp, facebook, web)
    channel: str = "web"
    user_id: str = ""
    
    # Extra data agents want to forward (e.g. list of found doctors)
    metadata: dict[str, Any] = Field(default_factory=dict)