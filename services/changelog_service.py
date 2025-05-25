from fastapi import HTTPException, status
from models import Event, EventChangelog, EventVersion, EventPermission
from deepdiff import DeepDiff
from services.event_service import make_json_serializable
from schemas.version import EventChangelogResponse

# Service to retrieve the chronological history of changes made to an event
def get_event_changelog_service(id, db, current_user):
    event = db.query(Event).filter(Event.id == id).first()
    if not event or (event.owner_id != current_user.id and not db.query(EventPermission).filter_by(event_id = id, user_id = current_user.id).first()):
        raise HTTPException(status_code=403, detail="Permission denied")
    changelog = db.query(EventChangelog).filter_by(event_id=id).order_by(EventChangelog.changed_at.asc()).all()
    valid_changelog = [entry for entry in changelog if entry.version_id is not None]

    return [EventChangelogResponse.model_validate(entry) for entry in valid_changelog]

# Service to get the diff between two versions of an event
def get_event_diff_service(id, version_id1, version_id2, db, current_user):
    event = db.query(Event).filter(Event.id == id).first()
    if not event or (event.owner_id !=  current_user.id and not db.query(EventPermission).filter_by(event_id = id, user_id = current_user.id).first()):
        raise HTTPException(status_code=403, detail="Permission denied")
    version1 = db.query(EventVersion).filter_by(event_id=id, version=version_id1).first()
    version2 = db.query(EventVersion).filter_by(event_id=id, version=version_id2).first()
    if not version1 or not version2:
        raise HTTPException(status_code=404, detail="Version not found")
    diff = DeepDiff(version1.data, version2.data, ignore_order=True).to_dict()
    diff = make_json_serializable(diff)
    return {"diff": diff}