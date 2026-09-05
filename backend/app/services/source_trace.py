def source_trace_fallback() -> list[dict]:
    return [
        {
            "date": "Unknown",
            "source": "Original upload",
            "platform": "Unverified",
            "caption": "No independent source was found in the MVP. The earliest available instance could not be independently confirmed.",
            "status": "Unverified"
        }
    ]


def source_trace_from_metadata(metadata: dict | None) -> list[dict]:
    events = []
    if metadata:
        exif = metadata.get("exif", {})
        if exif:
            creation_date = exif.get(36867) or exif.get(306) or exif.get("DateTimeOriginal")
            if creation_date:
                events.append({
                    "date": str(creation_date),
                    "source": "File creation",
                    "platform": "Local device",
                    "caption": f"EXIF creation date recorded as {creation_date}.",
                    "status": "Review"
                })
            software = exif.get(305) or exif.get("Software")
            if software:
                events.append({
                    "date": "Unknown",
                    "source": "Processing detected",
                    "platform": "Software",
                    "caption": f"File was processed by '{software}' before upload.",
                    "status": "Review"
                })
    if not events:
        events.append({
            "date": "Unknown",
            "source": "Original upload",
            "platform": "Unverified",
            "caption": "No provenance metadata was found. This is common for edited or AI-generated images.",
            "status": "Unverified"
        })
    return events
