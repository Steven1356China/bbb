from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models import Problem, Tag, ProblemTag, User
import json
from cryptography.fernet import Fernet
import os

bp = Blueprint('problems', __name__)

# 加密密钥
fernet = Fernet(os.environ.get('ENCRYPTION_KEY', Fernet.generate_key()))

@bp.route('/', methods=['GET'])
def get_problems():
    """获取题目列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    difficulty = request.args.get('difficulty')
    tag = request.args.get('tag')
    search = request.args.get('search')
    
    query = Problem.query.filter(Problem.status == 'approved')
    
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)
    if search:
        query = query.filter(Problem.title.ilike(f'%{search}%'))
    
    problems = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'problems': [p.to_dict() for p in problems.items],
        'total': problems.total,
        'pages': problems.pages,
        'page': page
    })

@bp.route('/<problem_id>', methods=['GET'])
def get_problem(problem_id):
    """获取题目详情"""
    problem = Problem.query.get_or_404(problem_id)
    
    # 只有管理员和出题人能查看未审核的题目
    current_user_id = get_jwt_identity()
    if problem.status != 'approved' and current_user_id != problem.created_by:
        jwt_data = get_jwt()
        if jwt_data.get('role') != 'admin':
            return jsonify({'error': '无权查看'}), 403
    
    response = problem.to_dict()
    response['tags'] = [tag.name for tag in problem.tags]
    
    return jsonify(response)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_problem():
    """创建题目"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['title', 'description', 'test_cases']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    # 加密测试用例
    encrypted_test_cases = fernet.encrypt(
        json.dumps(data['test_cases']).encode()
    ).decode()
    
    # 创建题目
    problem = Problem(
        title=data['title'],
        description=data['description'],
        input_description=data.get('input_description', ''),
        output_description=data.get('output_description', ''),
        difficulty=data.get('difficulty', 'medium'),
        time_limit=data.get('time_limit', 1000),
        memory_limit=data.get('memory_limit', 256),
        test_cases=encrypted_test_cases,
        score_config=data.get('score_config', {'total': 100}),
        languages=data.get('languages', ['cpp', 'python']),
        created_by=get_jwt_identity(),
        status='pending'
    )
    
    db.session.add(problem)
    db.session.flush()  # 获取ID但不提交
    
    # 处理标签
    for tag_name in data.get('tags', []):
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.flush()
        
        problem_tag = ProblemTag(problem_id=problem.id, tag_id=tag.id)
        db.session.add(problem_tag)
    
    db.session.commit()
    
    return jsonify(problem.to_dict()), 201

@bp.route('/<problem_id>', methods=['PUT'])
@jwt_required()
def update_problem(problem_id):
    """更新题目"""
    problem = Problem.query.get_or_404(problem_id)
    current_user_id = get_jwt_identity()
    
    # 只有出题人和管理员可以修改
    if current_user_id != problem.created_by:
        jwt_data = get_jwt()
        if jwt_data.get('role') != 'admin':
            return jsonify({'error': '无权修改'}), 403
    
    data = request.get_json()
    
    # 更新字段
    if 'title' in data:
        problem.title = data['title']
    if 'description' in data:
        problem.description = data['description']
    if 'difficulty' in data:
        problem.difficulty = data['difficulty']
    if 'test_cases' in data:
        problem.test_cases = fernet.encrypt(
            json.dumps(data['test_cases']).encode()
        ).decode()
    
    db.session.commit()
    
    return jsonify(problem.to_dict())

@bp.route('/admin/pending', methods=['GET'])
@jwt_required()
def get_pending_problems():
    """获取待审核题目列表（仅管理员）"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403
    
    problems = Problem.query.filter_by(status='pending').all()
    return jsonify([p.to_dict() for p in problems])

@bp.route('/admin/approve/<problem_id>', methods=['POST'])
@jwt_required()
def approve_problem(problem_id):
    """审核通过题目"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403
    
    problem = Problem.query.get_or_404(problem_id)
    problem.status = 'approved'
    db.session.commit()
    
    return jsonify({'message': '审核通过'})
