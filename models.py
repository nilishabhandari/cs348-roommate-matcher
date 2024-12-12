from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Profile(db.Model):
    __tablename__ = 'profile'
    profile_id = db.Column(db.Integer, primary_key=True)
    # Indexed for fast lookups
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)  
    # Indexed for fast lookups
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) 
    password_hash = db.Column(db.String(128), nullable=False)
    school_year = db.Column(db.String(50), nullable=False)
    # Indexed for search/report filtering
    residence = db.Column(db.String(100), index=True)  
    # Indexed for filtering
    gender = db.Column(db.String(10), nullable=False, index=True)  
    # Indexed for filtering
    smoker = db.Column(db.Boolean, default=False, index=True)  
    preferred_gender = db.Column(db.String(10), nullable=True)

    # Composite index for filtering by both gender and residence
    __table_args__ = (
        db.Index('idx_gender_residence', 'gender', 'residence'),
    )
