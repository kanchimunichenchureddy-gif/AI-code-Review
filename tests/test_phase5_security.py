from pathlib import Path
from analysis.security.engine import security_analysis_engine
from analysis.security.sandbox import docker_sandbox_runner


def test_security_engine_vulnerability_detections():
    vulnerable_code = """
import os
import pickle
import random
import hashlib

def login(user_input):
    # SQL Injection
    query = "SELECT * FROM users WHERE username = " + user_input
    
    # Command Injection
    os.system("ls " + user_input)
    
    # Path Traversal
    f = open("/tmp/" + user_input)
    
    # Weak Random
    token = random.random()
    
    # Hardcoded Secret
    password = "supersecretpassword123"
    
    # Insecure Deserialization
    data = pickle.loads(user_input)
    
    # Weak Cryptography
    h = hashlib.md5(user_input.encode()).hexdigest()
    
    # Secret Exposure
    print("User password is:", password)
    
    return query
"""
    findings = security_analysis_engine.scan_file("vuln.py", vulnerable_code)
    rule_ids = [f.cve_or_rule for f in findings]

    assert "SQL_INJECTION" in rule_ids
    assert "COMMAND_INJECTION" in rule_ids
    assert "PATH_TRAVERSAL" in rule_ids
    assert "WEAK_RANDOM" in rule_ids
    assert "HARDCODED_SECRET" in rule_ids
    assert "INSECURE_DESERIALIZATION" in rule_ids
    assert "WEAK_CRYPTOGRAPHY" in rule_ids
    assert "SECRET_EXPOSURE" in rule_ids


def test_security_engine_configuration_risk_detections():
    config_code = '''
DEBUG: bool = True
SECRET_KEY: str = "change_this_to_a_secure_secret_key_in_production"
DATABASE_URL: str = "sqlite:///./local.db"
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)
MYSQL_PASSWORD=medguard_password
'''
    findings = security_analysis_engine.scan_file("config.py", config_code)
    rule_ids = [f.cve_or_rule for f in findings]

    assert "DEBUG_ENABLED" in rule_ids
    assert "DEFAULT_SECRET" in rule_ids
    assert "INSECURE_DB_FALLBACK" in rule_ids
    assert "INSECURE_CORS" in rule_ids
    assert "PLAINTEXT_ENV_SECRET" in rule_ids


def test_docker_sandbox_runner_timeout(tmp_path):
    res = docker_sandbox_runner.run_isolated_command(tmp_path, "sleep 10")
    # Timeout after 5s
    assert res.timed_out is True
    assert res.exit_code == 124


def test_security_findings_api_endpoint(client, test_student, test_instructor):
    # Setup Course & Assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]
    
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS800", "title": "Cybersecurity & Secure Coding"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Security Lab", "language": "python"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student Submission
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    sub_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "security_test.py",
                    "content": "import os\ndef execute(cmd):\n    password = 'mypassword123'\n    os.system('ls ' + cmd)\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    sub_id = sub_res.json()["id"]

    # Trigger Full Analysis (which runs security scan)
    client.post(
        f"/api/v1/submissions/{sub_id}/analyze",
        headers={"Authorization": f"Bearer {std_token}"},
    )

    # Query Security Findings
    sec_res = client.get(
        f"/api/v1/submissions/{sub_id}/security-findings",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert sec_res.status_code == 200
    sec_findings = sec_res.json()
    assert len(sec_findings) >= 2
    cve_rules = [s["cve_or_rule"] for s in sec_findings]
    assert "COMMAND_INJECTION" in cve_rules
    assert "HARDCODED_SECRET" in cve_rules
