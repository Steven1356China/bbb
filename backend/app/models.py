from datetime import datetime
from app import db
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关系
    submissions = db.relationship('Submission', backref='author', lazy=True)
    created_problems = db.relationship('Problem', backref='creator', lazy=True)
    created_contests = db.relationship('Contest', backref='creator', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    input_description = db.Column(db.Text)
    output_description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')
    time_limit = db.Column(db.Integer, default=1000)  # ms
    memory_limit = db.Column(db.Integer, default=256)  # MB
    test_cases = db.Column(db.Text)  # 加密存储
    score_config = db.Column(db.JSON, default={'total': 100})
    languages = db.Column(db.JSON, default=['cpp', 'python'])
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 关系
    submissions = db.relationship('Submission', backref='problem', lazy=True)
    tags = db.relationship('Tag', secondary='problem_tags', backref='problems', lazy=True)
    contests = db.relationship('ContestProblem', backref='problem', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'time_limit': self.time_limit,
            'memory_limit': self.memory_limit,
            'created_by': self.created_by,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'languages': self.languages
        }

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#3b82f6')

class ProblemTag(db.Model):
    __tablename__ = 'problem_tags'
    
    problem_id = db.Column(db.String(36), db.ForeignKey('problems.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.String(36), db.ForeignKey('problems.id'), nullable=False)
    contest_id = db.Column(db.String(36), db.ForeignKey('contests.id'), nullable=True)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    result = db.Column(db.JSON)
    score = db.Column(db.Integer, default=0)
    execution_time = db.Column(db.Integer)
    memory_usage = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'problem_id': self.Problem_id,
            'language': self.language,
            'status': self.status,
            'score': self.score,
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Contest(db.Model):
    __tablename__ = 'contests'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    problems = db.relationship('ContestProblem', backref='contest', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('User', secondary='contest_participants', lazy='subquery',
                                  backref=db.backref('contests', lazy=True))

class ContestProblem(db.Model):
    __tablename__ = 'contest_problems'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    contest_id = db.Column(db.String(36), db.ForeignKey('contests.id'), nullable=False)
    problem_id = db.Column(db.String(36), db.ForeignKey('problems.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=100)
    
    __table_args__ = (db.UniqueConstraint('contest_id', 'problem_id'),)

class ContestParticipant(db.Model):
    __tablename__ = 'contest_participants'
    
    contest_id = db.Column(db.String(36), db.ForeignKey('contests.id'), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_score = db.Column(db.Integer, default=0)
