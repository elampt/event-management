from fastapi import HTTPException, status
from models import Event
from models.permission import EventPermission, RoleEnum
from schemas.permission import ShareEventRequest, PermissionResponse, UpdatePermissionRequest

# Service to share an event with other users
def share_event_service(id, share_req, db, current_user):
    event = db.query(Event).filter(Event.id == id).first()
    if not event or event.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission denied or event not found")
    
    for user in share_req.users:
        permission = db.query(EventPermission).filter_by(event_id=id, user_id=user.user_id).first()
        if permission:
            # Update existing permission
            permission.role = user.role
        else:
            # Create new permission
            new_permission = EventPermission(event_id=id, user_id=user.user_id, role=user.role)
            db.add(new_permission)
    db.commit()

    # Fetch updated permissions
    permissions = db.query(EventPermission).filter_by(event_id=id).all()
    return [PermissionResponse.model_validate({**perm.__dict__}) for perm in permissions]


# Service to get all permissions for an event
def get_event_permissions_service(id, db, current_user):
    event = db.query(Event).filter(Event.id == id).first()
    # Check if the event exists, and if the user is the owner or has any permission to the event
    has_permission = (event and (
        event.owner_id == current_user.id or
        db.query(EventPermission).filter_by(event_id=id, user_id=current_user.id).first()
    ))
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    # Owner as a virtual permission
    permissions = [
        PermissionResponse(user_id=event.owner_id, role=RoleEnum.owner)
    ]
    
    db_permission = db.query(EventPermission).filter_by(event_id=id).all()
    permissions += [PermissionResponse.model_validate({**perm.__dict__}) for perm in db_permission]
    return permissions


# Service to update an existing permission for a user for an event
def update_user_permission_service(id, user_id, update_req, db, current_user):
    event = db.query(Event).filter(Event.id == id).first()
    if not event or event.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Only the owner can update permissions")
    
    permission = db.query(EventPermission).filter_by(event_id=id, user_id=user_id).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    permission.role = update_req.role
    db.commit()
    db.refresh(permission)
    return PermissionResponse.model_validate({**permission.__dict__})


# Service to remove a user's permission for an event
def remove_user_permission_service(id, user_id, db, current_user):
    event = db.query(Event).filter(Event.id == id).first()
    if not event or event.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can remove permissions")
    
    permission = db.query(EventPermission).filter_by(event_id=id, user_id=user_id).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    
    db.delete(permission)
    db.commit()
    return