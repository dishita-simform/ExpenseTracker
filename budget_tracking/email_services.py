import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Sum, Count
from budget.models import Transaction, Category
import pandas as pd
import io
from django.contrib.auth import get_user_model
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from django.template.loader import render_to_string

User = get_user_model()

def get_email_template(template_name, context):
    """Render email template with context"""
    return render_to_string(f'emails/{template_name}.html', context)

def generate_monthly_report_pdf(user):
    # Get the first day of the current month
    today = datetime.now()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get transactions for the current month
    transactions = Transaction.objects.filter(
        user=user,
        date__range=[first_day, last_day]
    ).select_related('category').order_by('date')
    
    # Calculate summary statistics
    total_amount = transactions.aggregate(total=Sum('amount'))['total'] or 0
    transaction_count = transactions.count()
    
    # Get category-wise breakdown
    category_summary = transactions.values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph(f"Monthly Expense Report - {today.strftime('%B %Y')}", title_style))
    elements.append(Spacer(1, 12))
    
    # Add summary
    elements.append(Paragraph("Summary", styles['Heading2']))
    summary_data = [
        ["Total Expenses", f"₹{total_amount:,.2f}"],
        ["Number of Transactions", str(transaction_count)],
        ["Average Transaction", f"₹{(total_amount/transaction_count if transaction_count else 0):,.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Add category breakdown
    elements.append(Paragraph("Category Breakdown", styles['Heading2']))
    category_data = [["Category", "Amount", "Transactions"]]
    for cat in category_summary:
        category_data.append([
            cat['category__name'],
            f"₹{cat['total']:,.2f}",
            str(cat['count'])
        ])
    category_table = Table(category_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(category_table)
    elements.append(Spacer(1, 20))
    
    # Add recent transactions
    elements.append(Paragraph("Recent Transactions", styles['Heading2']))
    transaction_data = [["Date", "Category", "Description", "Amount"]]
    for trans in transactions.order_by('-date')[:10]:  # Show last 10 transactions
        transaction_data.append([
            trans.date.strftime('%Y-%m-%d'),
            trans.category.name if trans.category else 'Uncategorized',
            trans.description[:30] + '...' if len(trans.description) > 30 else trans.description,
            f"₹{trans.amount:,.2f}"
        ])
    trans_table = Table(transaction_data, colWidths=[1*inch, 1.5*inch, 2*inch, 1.5*inch])
    trans_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(trans_table)
    
    # Build PDF
    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def send_email_with_pdf(subject, body, pdf_data, user):
    sender_email = settings.EMAIL_HOST_USER
    sender_password = settings.EMAIL_HOST_PASSWORD
    recipient_email = user.email
    
    message = MIMEMultipart('alternative')
    message["From"] = f"Budget Tracker <{sender_email}>"
    message["To"] = recipient_email
    message["Subject"] = subject
    
    # Create HTML version of the email
    html_content = get_email_template('monthly_report', {
        'user': user,
        'month': datetime.now().strftime('%B %Y'),
        'body': body
    })
    
    # Add both plain text and HTML versions
    message.attach(MIMEText(body, "plain"))
    message.attach(MIMEText(html_content, "html"))
    
    # Attach PDF
    pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
    pdf_attachment.add_header('Content-Disposition', 'attachment', filename='monthly_report.pdf')
    message.attach(pdf_attachment)
    
    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
        print(f"Email sent successfully to {recipient_email}")
        
        server.quit()
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise

def send_monthly_report(user):
    subject = f"Monthly Expense Report - {datetime.now().strftime('%B %Y')}"
    body = f"""Hello {user.get_full_name() or user.username},

Please find attached your monthly expense report for {datetime.now().strftime('%B %Y')}.

This report includes:
- Summary of your monthly expenses
- Category-wise breakdown
- Recent transactions
- Total spending analysis

If you have any questions about your expenses, please don't hesitate to contact us.

Best regards,
Budget Tracker Team"""
    
    pdf_data = generate_monthly_report_pdf(user)
    send_email_with_pdf(subject, body, pdf_data, user)

def check_high_value_transactions(user):
    today = datetime.now().date()
    daily_total = Transaction.objects.filter(
        user=user,
        date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    if daily_total > 20000:
        # Get transaction details for the alert
        transactions = Transaction.objects.filter(
            user=user,
            date=today
        ).select_related('category').order_by('-amount')
        
        subject = "High Value Transaction Alert"
        
        # Create HTML content for the alert
        html_content = get_email_template('high_value_alert', {
            'user': user,
            'daily_total': daily_total,
            'transactions': transactions[:5],
            'date': today.strftime('%B %d, %Y')
        })
        
        # Plain text version
        body = f"""Hello {user.get_full_name() or user.username},

Alert: Your daily transactions have exceeded ₹20,000.

Current total: ₹{daily_total:,.2f}

Recent transactions:
"""
        
        # Add top 5 transactions to the email
        for trans in transactions[:5]:
            body += f"- {trans.date.strftime('%H:%M')} | {trans.category.name if trans.category else 'Uncategorized'} | ₹{trans.amount:,.2f}\n"
        
        body += """
Please review these transactions to ensure they are correct.

Best regards,
Budget Tracker Team"""
        
        recipient_email = user.email
        
        message = MIMEMultipart('alternative')
        message["From"] = f"Budget Tracker <{settings.EMAIL_HOST_USER}>"
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Add both plain text and HTML versions
        message.attach(MIMEText(body, "plain"))
        message.attach(MIMEText(html_content, "html"))
        
        try:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            text = message.as_string()
            server.sendmail(settings.EMAIL_HOST_USER, recipient_email, text)
            print(f"High value alert sent to {recipient_email}")
            
            server.quit()
        except Exception as e:
            print(f"Error sending high value alert: {str(e)}")
            raise 