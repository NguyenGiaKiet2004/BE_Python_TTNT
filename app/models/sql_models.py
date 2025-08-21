from sqlalchemy import Column, Integer, String, Enum, DateTime, Date, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from app.core.database import Base

class Department(Base):
    __tablename__ = 'Departments'
    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String(100), nullable=False)
    
class User(Base):
    __tablename__ = 'Users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('super_admin', 'hr_manager', 'employee'), default='employee')
    department_id = Column(Integer, ForeignKey('Departments.department_id'))
    
class FacialData(Base):
    __tablename__ = 'FacialData'
    face_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    encoding_data = Column(LargeBinary, nullable=False)
    reference_image_url = Column(String(255), nullable=False)

class AttendanceRecord(Base):
    __tablename__ = 'AttendanceRecords'
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    status = Column(Enum('on_time', 'late', 'absent'))
    record_date = Column(Date, nullable=False)

class SystemConfig(Base):
    __tablename__ = 'SystemConfigs'
    config_key = Column(String(50), primary_key=True)
    config_value = Column(String(255), nullable=False)
    description = Column(String(255))