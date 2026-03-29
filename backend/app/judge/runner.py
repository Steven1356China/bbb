import docker
import json
import time
import os
import tempfile
from pathlib import Path
from threading import Thread
from app.models import Submission, Problem
from app import db
import logging

logger = logging.getLogger(__name__)

class JudgeRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.test_cases_dir = Path('/tmp/test_cases')
        self.test_cases_dir.mkdir(exist_ok=True)
    
    def compile_code(self, code, language, work_dir):
        """编译代码"""
        if language == 'cpp':
            # 编译C++代码
            src_file = work_dir / 'solution.cpp'
            src_file.write_text(code)
            
            compile_result = self.client.containers.run(
                image='gcc:11',
                command=f'g++ -std=c++11 -O2 -o solution solution.cpp',
                working_dir='/app',
                volumes={str(work_dir): {'bind': '/app', 'mode': 'rw'}},
                remove=True
            )
            return 'solution'
        elif language == 'python':
            # Python无需编译
            src_file = work_dir / 'solution.py'
            src_file.write_text(code)
            return 'python3 solution.py'
    
    def run_test_case(self, input_data, expected_output, time_limit, memory_limit, language, work_dir):
        """运行单个测试用例"""
        try:
            # 创建输入文件
            input_file = work_dir / 'input.txt'
            input_file.write_text(input_data)
            
            if language == 'cpp':
                cmd = f'./solution'
                image = 'gcc:11'
            elif language == 'python':
                cmd = f'python3 solution.py'
                image = 'python:3.9-slim'
            
            # 运行容器
            container = self.client.containers.run(
                image=image,
                command=cmd,
                working_dir='/app',
                volumes={str(work_dir): {'bind': '/app', 'mode': 'rw'}},
                stdin_open=True,
                mem_limit=f'{memory_limit}m',
                network_mode='none',  # 禁用网络
                pids_limit=100,  # 限制进程数
                mem_swappiness=0,
                nano_cpus=int(1e9),  # 1 CPU核心
                detach=True
            )
            
            start_time = time.time()
            
            # 输入数据
            if input_data:
                socket = container.attach_socket(params={'stdin': 1, 'stream': 1})
                socket._sock.send(input_data.encode())
                socket._sock.send(b'\n')
                socket.close()
            
            # 等待结果
            result = container.wait(timeout=time_limit/1000 + 2)
            elapsed_time = (time.time() - start_time) * 1000  # 转换为ms
            
            # 获取输出
            output = container.logs(stdout=True, stderr=False).decode('utf-8', errors='ignore').strip()
            error = container.logs(stderr=True, stdout=False).decode('utf-8', errors='ignore').strip()
            
            container.remove(force=True)
            
            # 分析结果
            status = 'accepted'
            if result['StatusCode'] != 0:
                if elapsed_time > time_limit:
                    status = 'time_limit_exceeded'
                else:
                    status = 'runtime_error'
            elif elapsed_time > time_limit:
                status = 'time_limit_exceeded'
            else:
                # 比较输出
                if output.strip() != expected_output.strip():
                    status = 'wrong_answer'
            
            return {
                'status': status,
                'execution_time': int(elapsed_time),
                'output': output,
                'error': error
            }
            
        except Exception as e:
            logger.error(f"运行测试用例出错: {e}")
            return {
                'status': 'system_error',
                'execution_time': 0,
                'output': '',
                'error': str(e)
            }
    
    def judge_submission(self, submission_id):
        """评测提交"""
        submission = Submission.query.get(submission_id)
        if not submission:
            return
        
        problem = Problem.query.get(submission.problem_id)
        if not problem:
            submission.status = 'error'
            db.session.commit()
            return
        
        # 解析测试用例
        try:
            test_cases = json.loads(problem.test_cases)
        except:
            submission.status = 'error'
            db.session.commit()
            return
        
        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            
            # 编译代码
            try:
                exec_cmd = self.compile_code(submission.code, submission.language, work_dir)
            except Exception as e:
                submission.status = 'compile_error'
                submission.result = {'error': str(e)}
                db.session.commit()
                return
            
            # 运行测试用例
            results = []
            total_score = 0
            passed_cases = 0
            
            for i, test_case in enumerate(test_cases):
                result = self.run_test_case(
                    test_case['input'],
                    test_case['output'],
                    problem.time_limit,
                    problem.memory_limit,
                    submission.language,
                    work_dir
                )
                
                if result['status'] == 'accepted':
                    passed_cases += 1
                    # 计算分数
                    case_score = test_case.get('score', 100/len(test_cases))
                    total_score += case_score
                
                results.append({
                    'case_id': i + 1,
                    'status': result['status'],
                    'time': result['execution_time'],
                    'score': test_case.get('score', 100/len(test_cases)) if result['status'] == 'accepted' else 0
                })
            
            # 更新提交结果
            submission.status = 'accepted' if passed_cases == len(test_cases) else 'wrong_answer'
            submission.score = int(total_score)
            submission.result = {
                'test_cases': results,
                'passed': passed_cases,
                'total': len(test_cases)
            }
            
            db.session.commit()

def start_judge_worker():
    """启动评测工作者线程"""
    judge = JudgeRunner()
    
    while True:
        # 获取待评测的提交
        pending_submission = Submission.query.filter_by(
            status='pending'
        ).order_by(Submission.created_at.asc()).first()
        
        if pending_submission:
            pending_submission.status = 'judging'
            db.session.commit()
            
            judge.judge_submission(pending_submission.id)
        else:
            time.sleep(1)  # 无任务时等待
