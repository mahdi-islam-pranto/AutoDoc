from pydantic import BaseModel
from typing import Optional

# Pydantic model for incoming chat requests to API
class ChatRequest(BaseModel):
    message: str
    user_id: str        # phone number, FB PSID, etc.
    channel: str = "web"   # "web" | "whatsapp" | "facebook"
    
    
# Pydantic model for API responses
class ChatResponse(BaseModel):
    reply: str
    booking_stage: str
    thread_id: str
    selected_doctor: Optional[str] = None
    confirmation_id: Optional[str] = None