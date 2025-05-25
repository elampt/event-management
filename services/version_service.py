from fastapi import HTTPException, status
from models import Event, EventVersion, EventPermission, EventChangelog
from deepdiff import DeepDiff
from services.event_service import assign_version_data_to_event
from schemas.version import EventVersionSchema

# Service to retrieve the version history of an event
def get_event_version_service(id, version_id, db, current_user):
    version = db.query(EventVersion).filter_by(event_id=id, version=version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Permission check (owner or shared with other users)
    event = db.query(Event).filter(Event.id == id).first()
    if not event or (event.owner_id != current_user.id and not db.query(EventPermission).filter_by(event_id = id, user_id = current_user.id).first()):
        raise HTTPException(status_code=403, detail="Permission denied")
    return EventVersionSchema.model_validate(version)

# Service to rollback an event to a specific version
def rollback_event_service(id, version_id, db, current_user):
    try:
        version = db.query(EventVersion).filter_by(event_id=id, version=version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        event = db.query(Event).filter(Event.id == id).first()
        if not event or event.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Overwrite event fields with the version data
        assign_version_data_to_event(event, version.data)
        db.flush()

        latest_version = db.query(EventVersion).filter_by(event_id=id).order_by(EventVersion.version.desc()).first()
        next_version_number = (latest_version.version if latest_version else 0) + 1

        # Create a new version entry for the rollback
        new_version = EventVersion(
            event_id=id,
            version=next_version_number,
            data=version.data,
            changed_by=current_user.id,
            change_note="Rolled back to version {}".format(version.version)
        )
        db.add(new_version)
        db.flush()

        # Create a changelog entry for the rollback
        prev_version = latest_version
        diff = DeepDiff(prev_version.data, new_version.data, ignore_order=True).to_dict() if prev_version else {}
        change_log_entry = EventChangelog(
            event_id=id,
            version_id=new_version.id,
            diff=diff,
            changed_by=current_user.id,
        )
        db.add(change_log_entry)
        db.commit()
        db.refresh(new_version)
        return EventVersionSchema.model_validate(new_version)
    except Exception as e:
        db.rollback()
        print("Error during rollback:", e)
        raise HTTPException(status_code=500, detail="Failed to rollback event")