import logging
from datetime import datetime, date, timedelta, time
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db, SessionLocal
from app.models import sql_models
from app.models import schemas
from app.core.security import get_current_user

# --- Định nghĩa Schema phản hồi mới cho Check-in/Check-out ---
class SimpleResponse(BaseModel):
    message: str
    record_id: int

# --- Khởi tạo Router và Dependency ---
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.post(
    "/attendance/checkin",
    summary="Record a check-in",
    response_model=SimpleResponse
)
def check_in_endpoint(
    user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Records a check-in for the authenticated user.
    """
    now = datetime.now()
    today = now.date()
    
    existing_record = db.query(sql_models.AttendanceRecord).filter(
        sql_models.AttendanceRecord.user_id == user.user_id,
        sql_models.AttendanceRecord.record_date == today
    ).first()

    if existing_record and existing_record.check_in_time:
        raise HTTPException(status_code=400, detail="Check-in record for today already exists.")
    
    work_start_time_config = db.query(sql_models.SystemConfig).filter_by(config_key="work_start_time").first()
    late_threshold_config = db.query(sql_models.SystemConfig).filter_by(config_key="late_threshold").first()

    if not work_start_time_config or not late_threshold_config:
        logging.warning("System configuration for work start time or late threshold is missing. Using default values.")
        late_threshold_time = datetime.strptime("08:05:00", "%H:%M:%S").time()
    else:
        late_threshold_time = datetime.strptime(late_threshold_config.config_value, "%H:%M:%S").time()

    checkin_time_compare = now.time()
    
    status_of_checkin = "late" if checkin_time_compare > late_threshold_time else "on_time"

    new_record = sql_models.AttendanceRecord(
        user_id=user.user_id,
        check_in_time=now,
        record_date=today,
        status=status_of_checkin
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    logging.info(f"User {user.user_id} checked in successfully with status: {status_of_checkin}.")
    
    # --- Thay đổi tại đây ---
    return SimpleResponse(message="Check-in successful", record_id=new_record.record_id)


@router.post(
    "/attendance/checkout",
    summary="Record a check-out",
    response_model=SimpleResponse
)
def check_out_endpoint(
    user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Records a check-out for the authenticated user.
    """
    today = date.today()
    existing_record = db.query(sql_models.AttendanceRecord).filter(
        sql_models.AttendanceRecord.user_id == user.user_id,
        sql_models.AttendanceRecord.record_date == today
    ).first()

    if not existing_record or not existing_record.check_in_time:
        raise HTTPException(status_code=400, detail="Cannot check out. No check-in record found for today.")

    if existing_record.check_out_time:
        raise HTTPException(status_code=400, detail="Check-out record for today already exists.")

    existing_record.check_out_time = datetime.now()
    db.commit()
    db.refresh(existing_record)
    logging.info(f"User {user.user_id} checked out successfully.")
    
    # --- Thay đổi tại đây ---
    return SimpleResponse(message="Check-out successful", record_id=existing_record.record_id)


@router.get(
    "/attendance/history",
    response_model=List[schemas.AttendanceRecord],
    summary="Get attendance history for the current user"
)
def get_attendance_history(
    user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    start_date: Optional[date] = Query(None, description="Start date for the history"),
    end_date: Optional[date] = Query(None, description="End date for the history"),
    status_filter: Optional[str] = Query(None, description="Filter by status (e.g., 'on_time', 'late', 'absent')")
):
    """
    Retrieves attendance records for the authenticated user, with optional date and status filters.
    """
    query = db.query(sql_models.AttendanceRecord).filter(
        sql_models.AttendanceRecord.user_id == user.user_id
    )

    if start_date:
        query = query.filter(sql_models.AttendanceRecord.record_date >= start_date)
    if end_date:
        query = query.filter(sql_models.AttendanceRecord.record_date <= end_date)
    if status_filter:
        query = query.filter(sql_models.AttendanceRecord.status == status_filter)

    records = query.order_by(sql_models.AttendanceRecord.record_date.desc()).all()
    return records


@router.get(
    "/attendance/working-hours",
    summary="Calculate daily working hours"
)
def get_daily_working_hours(
    user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    start_date: Optional[date] = Query(None, description="Start date for calculation"),
    end_date: Optional[date] = Query(None, description="End date for calculation")
):
    """
    Calculates the total working hours for each day within a specified date range.
    """
    query = db.query(sql_models.AttendanceRecord).filter(
        sql_models.AttendanceRecord.user_id == user.user_id,
        sql_models.AttendanceRecord.check_in_time.isnot(None),
        sql_models.AttendanceRecord.check_out_time.isnot(None)
    )

    if start_date:
        query = query.filter(sql_models.AttendanceRecord.record_date >= start_date)
    if end_date:
        query = query.filter(sql_models.AttendanceRecord.record_date <= end_date)

    records = query.all()
    
    daily_hours: Dict[str, float] = {}
    for record in records:
        delta: timedelta = record.check_out_time - record.check_in_time
        hours = delta.total_seconds() / 3600
        daily_hours[str(record.record_date)] = round(hours, 2)
        
    return daily_hours

# import logging

# from datetime import datetime, date
# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.models import sql_models
# from app.models import schemas
# from app.core.security import get_current_user
# from typing import List
# from typing import Dict
# from datetime import timedelta
# from typing import Optional

# router = APIRouter()

# @router.post(
#     "/attendance/checkin",
#     summary="Record a check-in"
# )
# def check_in_endpoint(
#     user: sql_models.User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Records a check-in for the authenticated user.
#     """
#     today = date.today()
#     existing_record = db.query(sql_models.AttendanceRecord).filter(
#         sql_models.AttendanceRecord.user_id == user.user_id,
#         sql_models.AttendanceRecord.record_date == today
#     ).first()

#     if existing_record and existing_record.check_in_time:
#         raise HTTPException(status_code=400, detail="Check-in record for today already exists.")

#     new_record = sql_models.AttendanceRecord(
#         user_id=user.user_id,
#         check_in_time=datetime.now(),
#         record_date=today,
#         status="on_time" # Simplified status for now
#     )
#     db.add(new_record)
#     db.commit()
#     db.refresh(new_record)
#     logging.info(f"User {user.user_id} checked in successfully.")
#     return {"message": "Check-in successful", "record_id": new_record.record_id}

# @router.post(
#     "/attendance/checkout",
#     summary="Record a check-out"
# )
# def check_out_endpoint(
#     user: sql_models.User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Records a check-out for the authenticated user.
#     """
#     today = date.today()
#     existing_record = db.query(sql_models.AttendanceRecord).filter(
#         sql_models.AttendanceRecord.user_id == user.user_id,
#         sql_models.AttendanceRecord.record_date == today
#     ).first()

#     if not existing_record or not existing_record.check_in_time:
#         raise HTTPException(status_code=400, detail="Cannot check out. No check-in record found for today.")

#     if existing_record.check_out_time:
#         raise HTTPException(status_code=400, detail="Check-out record for today already exists.")

#     existing_record.check_out_time = datetime.now()
#     db.commit()
#     db.refresh(existing_record)
#     logging.info(f"User {user.user_id} checked out successfully.")
#     return {"message": "Check-out successful", "record_id": existing_record.record_id}

# @router.get(
#     "/attendance/history",
#     response_model=List[schemas.AttendanceRecord],
#     summary="Get attendance history for the current user"
# )
# def get_attendance_history(
#     user: sql_models.User = Depends(get_current_user),
#     db: Session = Depends(get_db),
#     start_date: Optional[date] = Query(None, description="Start date for the history"),
#     end_date: Optional[date] = Query(None, description="End date for the history"),
#     status_filter: Optional[str] = Query(None, description="Filter by status (e.g., 'on_time', 'late', 'absent')")
# ):
#     """
#     Retrieves attendance records for the authenticated user, with optional date and status filters.
#     """
#     query = db.query(sql_models.AttendanceRecord).filter(
#         sql_models.AttendanceRecord.user_id == user.user_id
#     )

#     if start_date:
#         query = query.filter(sql_models.AttendanceRecord.record_date >= start_date)
#     if end_date:
#         query = query.filter(sql_models.AttendanceRecord.record_date <= end_date)
#     if status_filter:
#         query = query.filter(sql_models.AttendanceRecord.status == status_filter)

#     records = query.order_by(sql_models.AttendanceRecord.record_date.desc()).all()
#     return records




# @router.get(
#     "/attendance/working-hours",
#     summary="Calculate daily working hours"
# )
# def get_daily_working_hours(
#     user: sql_models.User = Depends(get_current_user),
#     db: Session = Depends(get_db),
#     start_date: Optional[date] = Query(None, description="Start date for calculation"),
#     end_date: Optional[date] = Query(None, description="End date for calculation")
# ):
#     """
#     Calculates the total working hours for each day within a specified date range.
#     """
#     query = db.query(sql_models.AttendanceRecord).filter(
#         sql_models.AttendanceRecord.user_id == user.user_id,
#         sql_models.AttendanceRecord.check_in_time.isnot(None),
#         sql_models.AttendanceRecord.check_out_time.isnot(None)
#     )

#     if start_date:
#         query = query.filter(sql_models.AttendanceRecord.record_date >= start_date)
#     if end_date:
#         query = query.filter(sql_models.AttendanceRecord.record_date <= end_date)

#     records = query.all()
    
#     daily_hours: Dict[str, float] = {}
#     for record in records:
#         delta: timedelta = record.check_out_time - record.check_in_time
#         hours = delta.total_seconds() / 3600
#         daily_hours[str(record.record_date)] = round(hours, 2)
        
#     return daily_hours