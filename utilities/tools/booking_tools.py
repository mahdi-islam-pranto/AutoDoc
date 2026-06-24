import json
from langchain_core.tools import tool
# from graph.state import ConversationState
from config.db import get_postgresql_db_config 
import datetime
import asyncpg
from pydantic import BaseModel, Field
from typing import Literal
from dotenv import load_dotenv
load_dotenv()


# Helper to get a DB connection. 
async def get_conn():
    """Helper to get a DB connection."""
    db_config = get_postgresql_db_config()
    conn = await asyncpg.connect(
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"],
        user=db_config["user"],
        password=db_config["password"]
    )
    return conn
    


# test db operation tool
@tool
def db_operation_test(query: str) -> str:
    """Test database operation."""
    # update conversation state
    # ConversationState.tool_call_made = "db_operation_test"
    print(f"tool: Database operation tool called with query: {query}")
    return "Database operation tool call successful!"

# print("DB_URI from .env:", DB_URL)

# tool that interacts with the database to get available slots for a doctor on a given date.
@tool
async def get_available_slots(doctor_id: str) -> str:
    """
    Get available appointment slots for a doctor
    Args:
        doctor_id: The ID of the doctor.
    Returns a formatted string of available time slots.
    """
    conn = await get_conn()
    print(f"tool: get_available_slots called with doctor_id: {doctor_id}")

    try:
        # Fetch doctor's opening hours
        row = await conn.fetchrow(
            """
            SELECT name, opening_hours
            FROM doctors
            WHERE id = $1 AND is_active = TRUE
            """,
            int(doctor_id)
        )

        if not row:
            return f"No active doctor found with ID {doctor_id}."

        doctor_name = row["name"]
        opening_hours: dict = row["opening_hours"]

        
        print(f"tool: Doctor {doctor_name} has opening hours: {opening_hours}")
        
        return (
            f"Dr. {doctor_name} is available at the following times: {"sample times"}. "
            f"Opening hours: {', '.join(opening_hours)}. "
            f"Available slots: {', '.join(opening_hours)}."
        )
        
        

    except ValueError as e:
        return f"Error: {e}"
    finally:
        await conn.close()
    
    



# booking tool for book apppointment to the db

# input model for book_appointment tool
class BookAppointmentInput(BaseModel):
    doctor_id: int = Field(description="The integer ID of the doctor from the doctors table.")
    patient_name: str = Field(description="Full name of the patient.")
    patient_phone: str = Field(description="Patient's phone number.")
    patient_email: str | None = Field(default=None, description="Patient's email address (optional).")
    patient_age: int | None = Field(default=None, description="Patient's age in years (optional).")
    patient_gender: str | None = Field(default=None, description="Patient's gender (optional).")
    appointment_date: str = Field(description="Appointment date in YYYY-MM-DD format.")
    appointment_slot: str = Field(description="Chosen time slot in HH:MM (24hr) format, e.g. '16:00'.")
    visit_type: Literal["first_visit", "follow_up"] = Field(
        default="first_visit",
        description="Whether this is a first visit or a follow-up. Determines which fee applies."
    )
    notes: str | None = Field(default=None, description="Any extra notes from the patient (optional).")

# main tool to book appointment
@tool(args_schema=BookAppointmentInput)
async def book_appointment(
    doctor_id: int,
    patient_name: str,
    patient_phone: str,
    appointment_date: str,
    appointment_slot: str,
    patient_email: str | None = None,
    patient_age: int | None = None,
    patient_gender: str | None = None,
    visit_type: Literal["first_visit", "follow_up"] = "first_visit",
    notes: str | None = None,
) -> str:
    """
    Book a confirmed appointment for a patient with a doctor.
    Call this tool only after the user has explicitly confirmed all booking details.
    Inserts a new row into the appointments table and returns a confirmation summary
    for the agent to relay to the user.
    """
    conn = await get_conn()
    print(f"tool: book_appointment called — doctor_id={doctor_id}, date={appointment_date}, slot={appointment_slot}")

    try:
        # ── Step 1: Fetch doctor info & validate ──────────────────────────────
        doctor = await conn.fetchrow(
            """
            SELECT id, name, specialization_name, chamber_address,
                   first_visit_fee, follow_up_fee, avg_duration,
                   avg_load, reserved, opening_hours, is_active
            FROM doctors
            WHERE id = $1
            """,
            doctor_id,
        )
        
        # double check the doctor id matches with state selected doctor id for consistency
        if doctor_id != doctor["id"]:
            return f"There was a mismatch of doctor IDs. Please try confirming the doctor again."

        if not doctor:
            return f"Booking failed: No doctor found with ID {doctor_id}."

        if not doctor["is_active"]:
            return f"Booking failed: Dr. {doctor['name']} is currently inactive."
        # print 1st step doctor info for debugging
        print(f"tool: Doctor info — {dict(doctor)}")


        # ── Step 2: Validate that the slot falls within opening hours ─────────
        parsed_date = datetime.date.fromisoformat(appointment_date)
        day_name = parsed_date.strftime("%A").lower()           # e.g. "tuesday"
        
        opening_hours_raw = doctor["opening_hours"] or "{}"
        opening_hours: dict = (
            json.loads(opening_hours_raw)
            if isinstance(opening_hours_raw, str)
            else opening_hours_raw
        )
        
        day_ranges = opening_hours.get(day_name, [])            # e.g. ["16:00-18:00"]

        slot_time = datetime.time.fromisoformat(appointment_slot)  # e.g. time(16, 0)

        # Helper to check if the slot falls within any of the opening hour ranges for that day
        def slot_in_range(slot: datetime.time, ranges: list[str]) -> bool:
            for r in ranges:
                start_str, end_str = r.split("-")
                start = datetime.time.fromisoformat(start_str.strip())
                end   = datetime.time.fromisoformat(end_str.strip())
                if start <= slot < end:
                    return True
            return False

        if not day_ranges or not slot_in_range(slot_time, day_ranges):
            hours_display = ", ".join(day_ranges) if day_ranges else "not available"
            return (
                f"Booking failed: Dr. {doctor['name']} does not have a slot at "
                f"{appointment_slot} on {parsed_date.strftime('%A, %B %d %Y')}. "
                f"Opening hours for {day_name.capitalize()}: {hours_display}."
            )
            
            # print 2nd step slot validation result for debugging
        print(f"tool: Slot validation passed for {appointment_slot} on {parsed_date.strftime('%A, %B %d %Y')} (Opening hours: {', '.join(day_ranges)})")

        # ── Step 3: Check slot capacity for that day ──────────────────────────
        booked_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM appointments
            WHERE doctor_id = $1
              AND appointment_date = $2
              AND status NOT IN ('cancelled')
            """,
            doctor_id, parsed_date,
        )

        max_capacity = (doctor["avg_load"] or 20) - (doctor["reserved"] or 0)
        if booked_count >= max_capacity:
            return (
                f"Booking failed: Dr. {doctor['name']} is fully booked on "
                f"{parsed_date.strftime('%A, %B %d %Y')} "
                f"({booked_count}/{max_capacity} slots filled). Please choose another date."
            )
            
        # print 3rd step capacity check result for debugging
        print(f"tool: Capacity check passed for {parsed_date.strftime('%A, %B %d %Y')} (Booked: {booked_count}, Capacity: {max_capacity})")

        # ── Step 4: Check this exact slot isn't already taken ─────────────────
        slot_taken = await conn.fetchval(
            """
            SELECT COUNT(*) FROM appointments
            WHERE doctor_id = $1
              AND appointment_date = $2
              AND appointment_slot = $3
              AND status NOT IN ('cancelled')
            """,
            doctor_id, parsed_date, slot_time,
        )

        if slot_taken:
            return (
                f"Booking failed: The {appointment_slot} slot with Dr. {doctor['name']} "
                f"on {parsed_date.strftime('%B %d %Y')} is already taken. "
                f"Please choose a different time slot."
            )
            
        # print 4th step slot availability check for debugging
        print(f"tool: Slot availability check passed for {appointment_slot} on {parsed_date.strftime('%A, %B %d %Y')} (Slot taken: {slot_taken})")

        # ── Step 5: Compute serial number ───────────────────────────────
        serial_no = await conn.fetchval(
            """
            SELECT COALESCE(MAX(serial_no), 0) + 1
            FROM appointments
            WHERE doctor_id = $1 AND appointment_date = $2
            """,
            doctor_id, parsed_date,
        )

        # fee = (
        #     float(doctor["first_visit_fee"] or 0)
        #     if visit_type == "first_visit"
        #     else float(doctor["follow_up_fee"] or 0)
        # )

        # ── Step 6: Insert the appointment ────────────────────────────────────
        appointment_id = await conn.fetchval(
            """
            INSERT INTO appointments (
                doctor_id, patient_name, patient_phone, patient_email,
                patient_age, patient_gender, appointment_date, appointment_slot,
                visit_type, status, serial_no, booked_via, notes
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8,
                $9, 'confirmed', $10, 'ai_agent', $11
            )
            RETURNING id
            """,
            doctor_id, patient_name, patient_phone, patient_email,
            patient_age, patient_gender, parsed_date, slot_time,
            visit_type, serial_no, notes,
        )

        # ── Step 7: Return structured confirmation to the agent ───────────────
        date_display = parsed_date.strftime("%A, %B %d %Y")
        slot_display = datetime.datetime.strptime(appointment_slot, "%H:%M").strftime("%I:%M %p")

        # print final confirmation for debugging
        print(f"tool: Booking successful — Appointment ID: {appointment_id}, Serial No: {serial_no}")

        return (
            f"Appointment confirmed successfully!\n"
            f"──────────────────────────────\n"
            f"Appointment ID : #{appointment_id}\n"
            f"Serial No.     : {serial_no}\n"
            f"Doctor         : {doctor['name']}\n"
            f"Specialty      : {doctor['specialization_name']}\n"
            f"Chamber        : {doctor['chamber_address']}\n"
            f"Patient        : {patient_name}\n"
            f"Phone          : {patient_phone}\n"
            f"Date           : {date_display}\n"
            f"Time           : {slot_display}\n"
            f"Visit Type     : {visit_type.replace('_', ' ').title()}\n"
            # f"Fee            : ৳{fee:.2f}\n"
            f"──────────────────────────────\n"
            f"Please arrive 10 minutes early and bring this confirmation."
        )
        
        
    except asyncpg.UniqueViolationError:
        return "Booking failed: This slot was just taken by another booking. Please choose a different slot."
    except ValueError as e:
        return f"Booking failed due to invalid input: {e}"
    except Exception as e:
        print(f"tool: book_appointment error — {e}")
        return f"Booking failed due to an unexpected error: {e}"
    finally:
        await conn.close()