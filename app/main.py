from fastapi import Cookie
from fastapi import Form
from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi import UploadFile, File
from sqlalchemy import func, create_engine
from fastapi import HTTPException
from sqlalchemy import Column, Integer, String
from app.database import SessionLocal
from app.models import Upload, Error
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from io import BytesIO
from fastapi.responses import StreamingResponse

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

import logging 
logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
)


app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="upload.html"
    )


@app.post("/upload")
async def upload_file(
    request: Request,
    logfile: UploadFile = File(...)
):
    content = await logfile.read()

    with open(
        f"uploads/{logfile.filename}",
        "wb"
    ) as file:

        file.write(content)
    info_count = 0
    warning_count = 0
    error_count = 0
    error_groups = {}
    text = content.decode("utf-8")
    for line in text.splitlines():

        if line.startswith("INFO"):
            info_count += 1

        elif line.startswith("WARNING"):
            warning_count += 1

        elif line.startswith("ERROR"):
            error_count += 1
            message = line.replace("ERROR ", "")
            if message not in error_groups:
                error_groups[message] = 1
            else:
                error_groups[message] += 1

    db = SessionLocal()

    upload = Upload(
    filename=logfile.filename,
    info_count=info_count,
    warning_count=warning_count,
    error_count=error_count
    )

    db.add(upload)

    db.commit()
    logging.info(
            f"File uploaded:{logfile.filename}"
            )

    db.refresh(upload)
    for message, count in error_groups.items():

        error_record = Error(
            upload_id=upload.id,
            error_message=message,
            occurrence_count=count
        )      
        db.add(error_record)
    db.commit()
    
    db.close()
    return templates.TemplateResponse(
    request=request,
    name="result.html",

    context={
    "filename": logfile.filename,
    "info": info_count,
    "warning": warning_count,
    "error": error_count,
    "error_groups": error_groups
    }
)

@app.get("/upload/{upload_id}")
def upload_details(
        upload_id: int,
        logged_in: str = Cookie(default=None)
    ):
    if logged_in != "true":
        return RedirectResponse(
                url="/login",
                status_code=303
                )
    db = SessionLocal()

    upload = db.query(Upload).filter(
        Upload.id == upload_id
    ).first()

    errors = db.query(Error).filter(
        Error.upload_id == upload_id
    ).all()

    db.close()

    return {
        "upload": upload.filename,
        "errors": [
            {
                "message": error.error_message,
                "count": error.occurrence_count
            }
            for error in errors
        ]
    }


@app.get("/dashboard")
def dashboard(
    request: Request,
    logged_in: str = Cookie(default=None)
):

    if logged_in != "true":
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        total_uploads = db.query(Upload).count()

        total_info = db.query(
            func.sum(Upload.info_count)
        ).scalar() or 0

        total_warning = db.query(
            func.sum(Upload.warning_count)
        ).scalar() or 0

        total_error = db.query(
            func.sum(Upload.error_count)
        ).scalar() or 0

        recent_uploads = (
            db.query(Upload)
            .order_by(Upload.id.desc())
            .limit(5)
            .all()
        )

    finally:
        db.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_uploads": total_uploads,
            "total_info": total_info,
            "total_warning": total_warning,
            "total_error": total_error,
            "recent_uploads": recent_uploads
        }
    )


@app.get("/history")
def history(
        request: Request,
        logged_in: str = Cookie(default=None),
        search: str = "",
        page: int = 1
        ):

    if logged_in != "true":
        return RedirectResponse(
                url="/login", 
                status_code=303
    )
    db = SessionLocal()
    
    per_page = 5
    offset = (page - 1) * per_page
    total_uploads = (
            db.query(Upload)
            .filter(
                Upload.filename.contains(search)
                )
            .count()
            )
    total_pages = (total_uploads + per_page - 1) // per_page
    uploads = (
            db.query(Upload)
            .filter(
                Upload.filename.contains(search)
                )
            .order_by(
                Upload.id.desc()
                )
            .offset(offset)
            .limit(per_page)
            .all()
    )
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "uploads": uploads ,
            "search" : search,
            "page": page,
            "total_pages": total_pages
            }
    )

@app.get("/history/{upload_id}")
def upload_details(request: Request, upload_id: int):

    db = SessionLocal()

    upload = db.query(Upload).filter(
        Upload.id == upload_id
    ).first()

    errors = db.query(Error).filter(
        Error.upload_id == upload_id
    ).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="upload_details.html",
        context={
            "upload": upload,
            "errors": errors
        }
    )

@app.get("/api/uploads")
def api_uploads():

    db = SessionLocal()

    uploads = db.query(Upload).all()

    db.close()

    return uploads

@app.get("/api/uploads/{upload_id}")
def api_upload(upload_id: int):

    db = SessionLocal()

    upload = (
        db.query(Upload)
        .filter(Upload.id == upload_id)
        .first()
    )

    db.close()
    if not upload:
        logging.warning(
                f"Upload ID {upload_id} not found"
        )
        raise HTTPException(
                status_code=404,
                detail="Upload not found"
        )
    return upload

@app.get("/api/uploads/{upload_id}/errors")
def api_upload_errors(upload_id: int):

    db = SessionLocal()

    errors = (
        db.query(Error)
        .filter(Error.upload_id == upload_id)
        .all()
    )

    db.close()

    return errors



@app.get("/export/csv")
def export_csv(
    logged_in: str = Cookie(default=None)
    ):
    if logged_in != "true":
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    db = SessionLocal()

    uploads = (
        db.query(Upload)
        .order_by(Upload.id.desc())
        .all()
    )

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Filename",
        "INFO",
        "WARNING",
        "ERROR",
        "Uploaded At"
    ])

    for upload in uploads:

        writer.writerow([
            upload.id,
            upload.filename,
            upload.info_count,
            upload.warning_count,
            upload.error_count,
            upload.uploaded_at
        ])

    db.close()

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=log_report.csv"
        }
    )



@app.get("/export/pdf/{upload_id}")
def export_pdf(upload_id: int,
               logged_in: str = Cookie(default=None)
               ):
    if logged_in != "true":
        return RedirectResponse(
                url="/login",
                status_code=303
    )

    db = SessionLocal()

    upload = (
        db.query(Upload)
        .filter(Upload.id == upload_id)
        .first()
    )

    errors = (
        db.query(Error)
        .filter(Error.upload_id == upload_id)
        .all()
    )

    db.close()

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>Log Analysis Report</b>",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Filename:</b> {upload.filename}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>INFO:</b> {upload.info_count}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>WARNING:</b> {upload.warning_count}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>ERROR:</b> {upload.error_count}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph("<br/><b>Error Summary</b>", styles["Heading2"])
    )

    for error in errors:

        story.append(
            Paragraph(
                f"{error.error_message} : {error.occurrence_count}",
                styles["Normal"]
            )
        )

    doc.build(story)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            f"attachment; filename={upload.filename}.pdf"
        }
    )


@app.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...)
):

    if username == "admin" and password == "admin123":

        response = RedirectResponse(
            url="/dashboard",
            status_code=303
        )

        response.set_cookie(
            key="logged_in",
            value="true"
        )

        return response

    return RedirectResponse(
        url="/login",
        status_code=303
    )


@app.get("/logout")
def logout():

    response = RedirectResponse(
        url="/login",
        status_code=303
    )

    response.delete_cookie("logged_in")

    return response

