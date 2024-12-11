from datetime import datetime

from fastapi import FastAPI, HTTPException
from loguru import logger

app = FastAPI()

appointments = {
    datetime.strptime("2024-12-24 15:00", "%Y-%m-%d %H:%M").date(): [
        {
            "name": "test",
            "phone": "test",
            "time": datetime.strptime("2024-12-24 14:00", "%Y-%m-%d %H:%M").time(),
        },
        {
            "name": "test2",
            "phone": "test2",
            "time": datetime.strptime("2024-12-24 15:00", "%Y-%m-%d %H:%M").time(),
        },
    ]
}

logger.info(appointments)


@app.post("/")
async def create_appointment(name: str, phone: str, appointment_time: str):
    """
    Create an appointment with the given name, phone number, and appointment time.
    appointment_time should be in the format 'YYYY-MM-DD HH:MM'.
    """
    try:
        appointment_datetime = datetime.strptime(appointment_time, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD HH:MM'"
        )

    date_key = appointment_datetime.date()
    if date_key not in appointments:
        appointments[date_key] = []

    # Add the appointment
    appointments[date_key].append(
        {"name": name, "phone": phone, "time": appointment_datetime.time()}
    )

    logger.info(appointments)

    return {
        "message": "Appointment created successfully",
        "appointment_time": appointment_time,
    }


@app.get("/")
async def get_appointments(year: int, month: int, day: int):
    """
    Get all appointments for the given date without disclosing user data.
    """
    try:
        date_key = datetime(year, month, day).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date provided")

    if date_key not in appointments:
        return {"appointments": []}

    # Extract only time information for the appointments
    appointment_times = [appt["time"] for appt in appointments[date_key]]

    return {"appointments": appointment_times}
