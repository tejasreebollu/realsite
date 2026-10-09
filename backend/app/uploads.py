"""Owner-scoped uploads; validated raster images are served as resized JPEGs."""
import io
import os
import re
import uuid
import warnings
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from .models import UploadedImage, User

MAX_BYTES = 5 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000


def upload_directory():
    return Path(os.getenv("UPLOAD_DIR", "/app/uploads"))


def validate_uploaded_images(db, user, images):
    for url in images:
        if url.startswith("/api/uploads/"):
            asset = db.get(UploadedImage, url.split("/")[-1].removesuffix(".jpg"))
            if asset is None or asset.owner_id != user.id:
                raise HTTPException(422, "Use photos uploaded by your own account")
            if not (upload_directory() / f"{asset.id}.jpg").is_file():
                raise HTTPException(422, "An uploaded photo is unavailable; please upload it again")


def create_upload_router(current_user, database, rate_limit):
    router = APIRouter()
    @router.post("/api/uploads", status_code=201)
    def upload_image(request: Request, file: UploadFile = File(...),
                     user: User = Depends(current_user), db: Session = Depends(database)):
        rate_limit(request, "upload", 60)
        raw = file.file.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise HTTPException(413, "Each photo must be 5 MB or smaller")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(raw)) as source:
                    if source.format not in {"JPEG", "PNG", "WEBP"}:
                        raise HTTPException(422, "Choose a JPEG, PNG or WebP photo")
                    source.load()
                    image = ImageOps.exif_transpose(source).convert("RGBA")
                    image.thumbnail((2400, 2400))
                    clean = Image.new("RGB", image.size, "white")
                    clean.paste(image, mask=image.getchannel("A"))
                    output = io.BytesIO()
                    clean.save(output, "JPEG", quality=85, optimize=True)
                    width, height = clean.size
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise HTTPException(422, "This image cannot be read. Choose a smaller JPEG, PNG or WebP photo.")
        directory = upload_directory()
        directory.mkdir(parents=True, exist_ok=True)
        asset_id = uuid.uuid4().hex
        path = directory / f"{asset_id}.jpg"
        path.write_bytes(output.getvalue())
        try:
            db.add(UploadedImage(id=asset_id, owner_id=user.id, width=width, height=height))
            db.commit()
        except Exception:
            db.rollback()
            path.unlink(missing_ok=True)
            raise
        return {"url": f"/api/uploads/{asset_id}.jpg", "width": width, "height": height}


    @router.get("/api/uploads/{filename}", response_class=FileResponse)
    def uploaded_image(filename: str, db: Session = Depends(database)):
        if not re.fullmatch(r"[0-9a-f]{32}\.jpg", filename):
            raise HTTPException(404, "Photo not found")
        asset = db.get(UploadedImage, filename.removesuffix(".jpg"))
        path = upload_directory() / filename
        if asset is None or not path.is_file():
            raise HTTPException(404, "Photo not found")
        return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})
    return router
