from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid


def generate_ics_file(plan_data: Dict[str, Any], plan_id: str, race_name: str, race_date) -> str:
    """
    Generates ICS calendar content from training plan data
    """

    # ICS header
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RaceBuddy//Training Plan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Träningsplan - {race_name}",
        f"X-WR-CALDESC:Personlig träningsplan för {race_name}"
    ]

    # Add training sessions
    weeks = plan_data.get("weeks", [])

    for week in weeks:
        sessions = week.get("sessions", [])

        for session in sessions:
            event_lines = _create_training_event(session, plan_id)
            lines.extend(event_lines)

    # Add race date
    race_event_lines = _create_race_event(race_name, race_date, plan_id)
    lines.extend(race_event_lines)

    # ICS footer
    lines.append("END:VCALENDAR")

    return "\n".join(lines)


def _create_training_event(session: Dict[str, Any], plan_id: str) -> List[str]:
    """Creates ICS event for a training session"""

    # Get session data
    session_date = session.get("date")
    session_type = session.get("type", "Träning")
    description = session.get("description", "")
    distance = session.get("distance_km")
    pace = session.get("pace")
    intensity = session.get("intensity", "")

    # Convert date
    if isinstance(session_date, str):
        event_date = datetime.fromisoformat(session_date).date()
    else:
        event_date = session_date

    # Standard training time: 06:00-07:00
    start_time = datetime.combine(
        event_date, datetime.min.time().replace(hour=6))
    end_time = start_time + timedelta(hours=1)

    # Format dates for ICS
    start_ics = start_time.strftime("%Y%m%dT%H%M%S")
    end_ics = end_time.strftime("%Y%m%dT%H%M%S")
    created_ics = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    # Build title - use session description as main title
    title = session.get("description", session.get("type", "Träning"))

    # Build description - use notes (focus) as primary description
    desc_parts = []
    if session.get("notes"):  # This is "focus" from the AI plan
        desc_parts.append(f"Fokus: {session['notes']}")

    if session.get("type"):
        desc_parts.append(f"Typ: {session['type']}")

    if distance and pace:
        estimated_time = _estimate_session_time(distance, pace)
        if estimated_time:
            desc_parts.append(f"Beräknad tid: {estimated_time}")

    if session.get("intensity"):
        desc_parts.append(f"Intensitet: {session['intensity']}")

    desc_parts.append("\\n\\nGenererad av RaceBuddy")
    full_description = "\\n".join(desc_parts)

    # Generate unique UID
    event_uid = f"{plan_id}-{event_date.isoformat()}-{uuid.uuid4().hex[:8]}@racebuddy.com"

    return [
        "BEGIN:VEVENT",
        f"UID:{event_uid}",
        f"DTSTAMP:{created_ics}",
        f"DTSTART:{start_ics}",
        f"DTEND:{end_ics}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:{full_description}",
        "CATEGORIES:Träning",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
        # Reminder 30 minutes before
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Dags för träning!",
        "TRIGGER:-PT30M",
        "END:VALARM",
        "END:VEVENT"
    ]


def _create_race_event(race_name: str, race_date, plan_id: str) -> List[str]:
    """Creates ICS event for race day"""

    # Convert date
    if isinstance(race_date, str):
        event_date = datetime.fromisoformat(race_date).date()
    else:
        event_date = race_date

    # Race start usually in the morning
    start_time = datetime.combine(
        event_date, datetime.min.time().replace(hour=9))
    end_time = start_time + timedelta(hours=4)  # Generous time to finish

    # Format dates for ICS
    start_ics = start_time.strftime("%Y%m%dT%H%M%S")
    end_ics = end_time.strftime("%Y%m%dT%H%M%S")
    created_ics = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    # Generate unique UID
    event_uid = f"{plan_id}-race-{event_date.isoformat()}@racebuddy.com"

    description = f"TÄVLINGSDAG! {race_name}\\n\\nDu har tränat hårt för denna dag. Lycka till!\\n\\nTips:\\n- Ät bra frukost 2-3 timmar före start\\n- Värm upp ordentligt\\n- Kör enligt plan\\n\\nGenererad av RaceBuddy"

    return [
        "BEGIN:VEVENT",
        f"UID:{event_uid}",
        f"DTSTAMP:{created_ics}",
        f"DTSTART:{start_ics}",
        f"DTEND:{end_ics}",
        f"SUMMARY:🏃‍♂️🏆 {race_name} - TÄVLINGSDAG!",
        f"DESCRIPTION:{description}",
        "CATEGORIES:Tävling",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
        "PRIORITY:9",
        # Reminder the day before
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Imorgon är det tävling! Förbered utrustning och mental förberedelse.",
        "TRIGGER:-P1D",
        "END:VALARM",
        # Reminder 2 hours before
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Tävlingsdag! Ät frukost och börja förbereda dig.",
        "TRIGGER:-PT2H",
        "END:VALARM",
        "END:VEVENT"
    ]


def _estimate_session_time(distance_km: float, pace: str) -> str:
    """Calculates estimated session time based on distance and pace"""
    try:
        # Parse pace (format: "5:30")
        pace_parts = pace.split(":")
        if len(pace_parts) != 2:
            return None

        minutes = int(pace_parts[0])
        seconds = int(pace_parts[1])
        pace_seconds = minutes * 60 + seconds

        # Calculate total time
        total_seconds = int(distance_km * pace_seconds)

        # Convert to hours:minutes
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}:{minutes:02d}h"
        else:
            return f"{minutes} min"

    except (ValueError, AttributeError):
        return None
