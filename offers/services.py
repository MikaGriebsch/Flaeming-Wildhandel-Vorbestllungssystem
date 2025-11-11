from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Iterable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from offers.models import EmailLog, Registration


def _build_message(subject: str, template_prefix: str, to: list[str], context: dict) -> EmailMultiAlternatives:
    context = {**context, "subject": subject}
    html_body = render_to_string(f"email/{template_prefix}.html", context)
    text_body = render_to_string(f"email/{template_prefix}.txt", context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    message.attach_alternative(html_body, "text/html")
    return message


def log_email(registration: Registration | None, offer, recipient: str, typ: str, message_id: str = "gesendet"):
    EmailLog.objects.create(
        registration=registration,
        offer=offer,
        empfaenger=recipient,
        typ=typ,
        nachricht_id=message_id,
    )


def send_registration_confirmation(registration: Registration):
    offer = registration.offer
    user = registration.user
    context = {
        "registration": registration,
        "offer": offer,
        "user": user,
        "abhol_von": offer.abhol_von.strftime("%d.%m.%Y"),
        "abhol_bis": offer.abhol_bis.strftime("%d.%m.%Y"),
    }
    subject = f"Bestätigung deiner Vorbestellung: {offer.titel}"
    message = _build_message(subject, "order_confirmation", [user.email], context)
    message.send()
    log_email(registration, offer, user.email, EmailLog.Typ.CONFIRM)


def send_reminder_email(registration: Registration, reminder_type: str):
    offer = registration.offer
    user = registration.user
    context = {
        "registration": registration,
        "offer": offer,
        "user": user,
        "abhol_von": offer.abhol_von.strftime("%d.%m.%Y"),
        "abhol_bis": offer.abhol_bis.strftime("%d.%m.%Y"),
    }
    subjects = {
        EmailLog.Typ.REMINDER_PRE: f"Erinnerung: Deine Abholung startet bald ({offer.titel})",
        EmailLog.Typ.REMINDER_START: f"Heute startet die Abholung ({offer.titel})",
    }
    template_map = {
        EmailLog.Typ.REMINDER_PRE: "reminder_pre",
        EmailLog.Typ.REMINDER_START: "reminder_start",
    }
    subject = subjects.get(reminder_type, f"Information zu {offer.titel}")
    template_prefix = template_map.get(reminder_type, "reminder_pre")
    message = _build_message(subject, template_prefix, [user.email], context)
    message.send()
    log_email(registration, offer, user.email, reminder_type)


HEADER = [
    "Nr.",
    "Produkt",
    "Menge",
    "Nachname",
    "Vorname",
    "Straße",
    "Hausnr.",
    "PLZ",
    "Stadt",
]


def registration_rows(registrations: Iterable[Registration]):
    for index, registration in enumerate(registrations, start=1):
        user = registration.user
        yield [
            index,
            registration.offer.titel,
            registration.menge,
            user.last_name,
            user.first_name,
            user.street,
            user.house_number,
            user.postal_code,
            user.city,
        ]


def ordered_registrations(queryset):
    return queryset.select_related("user", "offer").order_by("user__last_name", "user__postal_code")


def export_registrations_csv(offer):
    queryset = ordered_registrations(offer.registrations.all())
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Angebot", offer.titel])
    writer.writerow([
        "Abholfenster",
        f"{offer.abhol_von.strftime('%d.%m.%Y')} – {offer.abhol_bis.strftime('%d.%m.%Y')}",
    ])
    writer.writerow([])
    writer.writerow(HEADER)
    for row in registration_rows(queryset):
        writer.writerow(row)
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename=vorbestellungen-{offer.slug}.csv"
    return response


def export_registrations_excel(offer):
    queryset = ordered_registrations(offer.registrations.all())
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Vorbestellungen"
    sheet.append(["Angebot", offer.titel])
    sheet.append([
        "Abholfenster",
        f"{offer.abhol_von.strftime('%d.%m.%Y')} – {offer.abhol_bis.strftime('%d.%m.%Y')}",
    ])
    sheet.append([])
    sheet.append(HEADER)
    for row in registration_rows(queryset):
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename=vorbestellungen-{offer.slug}.xlsx"
    return response


def export_registrations_pdf(offer):
    queryset = ordered_registrations(offer.registrations.all())
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph(f"{offer.titel}", styles["Title"])
    window = Paragraph(
        f"Abholfenster: {offer.abhol_von.strftime('%d.%m.%Y')} – {offer.abhol_bis.strftime('%d.%m.%Y')}",
        styles["Normal"],
    )
    story.extend([title, Spacer(1, 12), window, Spacer(1, 12)])

    data = [HEADER]
    data.extend(registration_rows(queryset))

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=vorbestellungen-{offer.slug}.pdf"
    return response
