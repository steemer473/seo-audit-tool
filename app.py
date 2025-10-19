"""
SEO Audit Tool - FastAPI Application
Main application with routes and background task processing
"""
from fastapi import FastAPI, Form, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import uuid
import os
import asyncio
import httpx
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

from database import Database, get_database
from audit_engine import run_seo_audit
from scoring import calculate_seo_score
from report_generator import generate_pdf_report

# Load environment variables
load_dotenv()

# Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/audit.db')
PDF_STORAGE_PATH = os.getenv('PDF_STORAGE_PATH', './data/reports')
DRAFT_STORAGE_PATH = os.getenv('DRAFT_STORAGE_PATH', './data/drafts')
GHL_WEBHOOK_URL = os.getenv('GHL_WEBHOOK_URL')
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
MAX_CONCURRENT_AUDITS = int(os.getenv('MAX_CONCURRENT_AUDITS', '10'))
AUDIT_TIMEOUT = int(os.getenv('AUDIT_TIMEOUT_SECONDS', '300'))
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')

# Ensure directories exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(PDF_STORAGE_PATH, exist_ok=True)
os.makedirs(DRAFT_STORAGE_PATH, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="SEO Audit Tool",
    description="Automated SEO audit reports for Level Play Digital",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database
db: Optional[Database] = None

# Semaphore for concurrent audit limiting
audit_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AUDITS)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    global db
    db = get_database(DATABASE_PATH, SECRET_KEY)
    await db.initialize()

    # Schedule cleanup task
    asyncio.create_task(periodic_cleanup())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass


async def periodic_cleanup():
    """Periodically clean up expired reports"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await db.cleanup_expired_reports()
        except Exception as e:
            print(f"Cleanup error: {e}")


# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing page with audit form"""
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/audit/submit")
async def submit_audit(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    report_type: str = Form('free'),
):
    """Submit audit request"""

    # Validate inputs
    if not url or not email or not first_name or not last_name:
        raise HTTPException(status_code=400, detail="All fields are required")

    # Generate unique UUID
    report_uuid = str(uuid.uuid4())

    # Create report in database
    report_id = await db.create_report(
        uuid=report_uuid,
        url=url,
        email=email,
        first_name=first_name,
        last_name=last_name,
        report_type=report_type
    )

    await db.log_event(report_uuid, 'submitted', f"Report submitted for {url}")

    # Send to GHL webhook for lead capture
    if GHL_WEBHOOK_URL:
        background_tasks.add_task(send_to_ghl, email, first_name, last_name, url, report_type)

    # Start audit in background
    background_tasks.add_task(process_audit, report_uuid, url)

    # Redirect to processing page
    return JSONResponse({
        "success": True,
        "report_uuid": report_uuid,
        "redirect_url": f"/audit/processing/{report_uuid}"
    })


@app.get("/audit/processing/{report_uuid}", response_class=HTMLResponse)
async def processing_page(request: Request, report_uuid: str):
    """Processing page with status updates"""
    report = await db.get_report(report_uuid)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return templates.TemplateResponse("processing.html", {
        "request": request,
        "report_uuid": report_uuid,
        "url": report['url']
    })


@app.get("/audit/status/{report_uuid}")
async def get_audit_status(report_uuid: str):
    """Get audit status (for AJAX polling)"""
    report = await db.get_report(report_uuid)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return JSONResponse({
        "status": report['status'],
        "error_message": report.get('error_message'),
        "completed_at": report.get('completed_at'),
    })


@app.get("/audit/complete/{report_uuid}", response_class=HTMLResponse)
async def complete_page(request: Request, report_uuid: str):
    """Completion page with download link"""
    report = await db.get_report(report_uuid)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Report not ready yet")

    return templates.TemplateResponse("complete.html", {
        "request": request,
        "report_uuid": report_uuid,
        "url": report['url'],
        "score": report['score'],
        "first_name": report['first_name'],
    })


@app.get("/audit/download/{report_uuid}")
async def download_report(report_uuid: str):
    """Download PDF report"""
    report = await db.get_report(report_uuid)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Report not ready")

    pdf_path = report['pdf_path']

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    # Log download
    await db.log_event(report_uuid, 'downloaded', 'Report downloaded')

    domain = report['url'].replace('https://', '').replace('http://', '').split('/')[0]
    filename = f"SEO-Audit-{domain}-{datetime.now().strftime('%Y%m%d')}.pdf"

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Background Tasks

async def process_audit(report_uuid: str, url: str):
    """Process audit in background"""
    async with audit_semaphore:
        try:
            await db.update_report_status(report_uuid, 'processing')
            await db.log_event(report_uuid, 'processing', 'Audit started')

            # Run audit
            audit_data = await run_seo_audit(url)
            await db.log_event(report_uuid, 'data_collected', 'Data collection complete')

            # Calculate score
            score_data = calculate_seo_score(audit_data)
            await db.log_event(report_uuid, 'scored', f"Score calculated: {score_data['total_score']}")

            # Generate PDF
            pdf_filename = f"report_{report_uuid}.pdf"
            pdf_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)

            generate_pdf_report(
                audit_data=audit_data,
                score_data=score_data,
                output_path=pdf_path,
                report_type='free'
            )

            await db.log_event(report_uuid, 'pdf_generated', 'PDF report generated')

            # Mark as completed
            await db.complete_report(
                uuid=report_uuid,
                pdf_path=pdf_path,
                audit_data=audit_data,
                score=score_data['total_score']
            )

            await db.log_event(report_uuid, 'completed', 'Audit completed successfully')

            # Send email with download link
            report = await db.get_report(report_uuid)
            await send_report_email(report)

        except Exception as e:
            error_message = str(e)
            await db.update_report_status(report_uuid, 'failed', error_message)
            await db.log_event(report_uuid, 'failed', f"Error: {error_message}")
            print(f"Audit failed for {report_uuid}: {error_message}")


async def send_to_ghl(email: str, first_name: str, last_name: str, url: str, report_type: str):
    """Send lead data to Go High Level webhook"""
    if not GHL_WEBHOOK_URL:
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                GHL_WEBHOOK_URL,
                json={
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name,
                    "website": url,
                    "reportType": report_type,
                    "source": "SEO Audit Tool",
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=10.0
            )
    except Exception as e:
        print(f"GHL webhook error: {e}")


async def send_report_email(report: dict):
    """Send report email via GHL (or other email service)"""
    # TODO: Implement email sending
    # For now, this is a placeholder
    # You can integrate with GHL's email API or use another service

    download_url = f"{BASE_URL}/audit/complete/{report['uuid']}"

    print(f"Email would be sent to: {report['email']}")
    print(f"Download URL: {download_url}")

    # Example GHL email API call (implement as needed)
    """
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.gohighlevel.com/v1/emails",
            headers={"Authorization": f"Bearer {GHL_API_KEY}"},
            json={
                "to": report['email'],
                "subject": f"Your SEO Audit Report is Ready - Score: {report['score']}/100",
                "body": f"Hi {report['first_name']},\n\nYour SEO audit for {report['url']} is complete!\n\nOverall Score: {report['score']}/100\n\nDownload your report: {download_url}\n\nBest,\nLevel Play Digital",
            }
        )
    """


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
