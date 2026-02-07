from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
import heapq
import logging

logger = logging.getLogger(__name__)


class AppointmentPriorityQueue:
    """
    DSA-based Priority Queue for scheduling appointments.
    Uses a min-heap to efficiently sort appointments by:
    1. Priority level (Critical > Medium > Normal)
    2. Date and time (earlier appointments first within same priority)
    """

    # Priority mapping (lower number = higher priority for min-heap)
    PRIORITY_VALUES = {"critical": 1, "medium": 2, "normal": 3}

    def __init__(self, appointments=None):
        """
        Initialize the priority queue with optional list of appointments.

        Args:
            appointments: QuerySet or list of Appointment objects
        """
        self.heap = []
        if appointments:
            for appointment in appointments:
                self.add_appointment(appointment)

    def add_appointment(self, appointment):
        """
        Add an appointment to the priority queue.

        Args:
            appointment: Appointment model instance
        """
        priority_value = self.PRIORITY_VALUES.get(appointment.priority, 3)

        # Combine date and time for accurate datetime comparison
        appointment_datetime = datetime.combine(appointment.date, appointment.time)

        # Create tuple for heap: (priority, datetime, appointment_id, appointment)
        # Using appointment.id as tiebreaker to ensure stable sorting
        heap_item = (priority_value, appointment_datetime, appointment.id, appointment)

        heapq.heappush(self.heap, heap_item)

    def get_sorted_appointments(self):
        """
        Return all appointments sorted by priority.
        Does not modify the original heap.

        Returns:
            List of Appointment objects sorted by priority and datetime
        """
        # Create a copy of the heap to avoid modifying original
        heap_copy = self.heap.copy()
        sorted_appointments = []

        while heap_copy:
            _, _, _, appointment = heapq.heappop(heap_copy)
            sorted_appointments.append(appointment)

        return sorted_appointments

    def peek(self):
        """
        View the highest priority appointment without removing it.

        Returns:
            Appointment object or None if queue is empty
        """
        if self.heap:
            return self.heap[0][3]
        return None

    def pop(self):
        """
        Remove and return the highest priority appointment.

        Returns:
            Appointment object or None if queue is empty
        """
        if self.heap:
            _, _, _, appointment = heapq.heappop(self.heap)
            return appointment
        return None

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.heap) == 0

    def size(self):
        """Return the number of appointments in the queue."""
        return len(self.heap)


def get_prioritized_appointments(appointments):
    """
    Utility function to get appointments sorted by priority using the priority queue.

    Args:
        appointments: QuerySet or list of Appointment objects

    Returns:
        List of Appointment objects sorted by priority
    """
    pq = AppointmentPriorityQueue(appointments)
    return pq.get_sorted_appointments()


def classify_appointment_priority(reason: str) -> str:
    """
    Uses AI (LLM) to classify appointment reason into priority levels.

    Args:
        reason: The patient's appointment reason/description

    Returns:
        'critical', 'medium', or 'normal'
    """
    try:
        # Initialize LLM
        api_key = getattr(settings, "GOOGLE_GENAI_API_KEY", None)
        if not api_key:
            return "normal"  # Default fallback

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", temperature=0.1, api_key=api_key
        )

        # Classification prompt
        prompt = f"""You are a medical triage AI assistant. Classify the following appointment reason into one of three priority levels based on medical urgency:

**Priority Levels:**
- CRITICAL: Life-threatening conditions, severe symptoms requiring immediate attention (e.g., chest pain, severe bleeding, difficulty breathing, stroke symptoms, severe injuries, high fever in infants, suspected heart attack)
- MEDIUM: Concerning symptoms that need prompt medical attention but not immediately life-threatening (e.g., persistent pain, moderate fever, infections, chronic condition flare-ups, injuries requiring evaluation)
- NORMAL: Routine health concerns, preventive care, follow-ups, minor ailments (e.g., common cold, routine check-ups, vaccination, minor skin issues, general health questions)

**Appointment Reason:**
{reason}

**Instructions:**
Analyze the medical urgency and respond with ONLY ONE WORD - either "critical", "medium", or "normal" (lowercase). No explanation needed.

**Classification:**"""

        # Get classification
        response = llm.invoke(prompt)
        classification = response.content.strip().lower()

        # Validate response
        if classification in ["critical", "medium", "normal"]:
            return classification
        else:
            # If unclear, default to normal
            return "normal"

    except Exception as e:
        print(f"Priority classification error: {e}")
        return "normal"  # Safe fallback


def send_appointment_email(appointment, created=False):
    """Send role-specific appointment emails to villager and health worker."""
    try:
        _send_appointment_email_impl(appointment, created)
    except Exception as e:
        logger.error(
            f"Failed to send appointment email for appointment #{appointment.pk}: {e}",
            exc_info=True,
        )


def _send_appointment_email_impl(appointment, created=False):
    """Internal implementation for sending appointment emails."""
    date_str = appointment.date.strftime("%b %d, %Y")
    time_str = appointment.time.strftime("%I:%M %p")

    # Determine subject line based on action
    if created:
        subject = f"Appointment Confirmed — {date_str} at {time_str}"
    elif appointment.status == "approved":
        subject = f"Appointment Approved — {date_str} at {time_str}"
    elif appointment.status == "completed":
        subject = f"Appointment Completed — {date_str}"
    elif appointment.status == "cancelled":
        subject = f"Appointment Cancelled — {date_str}"
    else:
        subject = f"Appointment Updated — {date_str} at {time_str}"

    # Send to villager
    if appointment.villager and appointment.villager.email:
        context = {
            "appointment": appointment,
            "created": created,
            "recipient_role": "villager",
        }
        text_content = render_to_string("appointments/email.txt", context)
        html_content = render_to_string("appointments/email.html", context)

        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.villager.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        logger.info(
            f"Email sent to villager {appointment.villager.email} for appointment #{appointment.pk}"
        )
    else:
        logger.warning(
            f"No villager email for appointment #{appointment.pk}, skipping villager notification"
        )

    # Send to health worker (if assigned)
    if appointment.healthworker and appointment.healthworker.email:
        patient_name = (
            f"{appointment.villager.first_name} {appointment.villager.last_name}"
        )
        if created:
            hw_subject = f"New Patient Appointment — {patient_name} on {date_str}"
        else:
            hw_subject = f"Appointment Update — {patient_name} on {date_str}"

        context = {
            "appointment": appointment,
            "created": created,
            "recipient_role": "health_worker",
        }
        text_content = render_to_string("appointments/email.txt", context)
        html_content = render_to_string("appointments/email.html", context)

        email = EmailMultiAlternatives(
            hw_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.healthworker.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        logger.info(
            f"Email sent to health worker {appointment.healthworker.email} for appointment #{appointment.pk}"
        )
    else:
        logger.info(
            f"No health worker assigned for appointment #{appointment.pk}, skipping HW notification"
        )
