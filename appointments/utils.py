from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_appointment_email(appointment, created=False):
    subject = 'New Appointment Created' if created else 'Appointment Updated'
    recipients = [appointment.villager.email]
    if created and appointment.healthworker:
        recipients.append(appointment.healthworker.email)
    recipients = [email for email in recipients if email]

    if recipients:
        context = {'appointment': appointment}
        text_content = render_to_string('appointments/email.txt', context)
        html_content = render_to_string('appointments/email.html', context)

        email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, recipients)
        email.attach_alternative(html_content, "text/html")
        email.send()
