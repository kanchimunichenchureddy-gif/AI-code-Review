from analysis.parsers.detector import language_detector


def test_language_detector_by_extension_and_content():
    # Extension detection
    assert language_detector.detect_language("script.py") == "python"
    assert language_detector.detect_language("app.js") == "javascript"
    assert language_detector.detect_language("Main.java") == "java"
    assert language_detector.detect_language("main.c") == "c"
    assert language_detector.detect_language("matrix.cpp") == "cpp"
    assert language_detector.detect_language("Program.cs") == "csharp"

    # Content keyword fallback when filename extension is unknown (.txt)
    py_code = "def fibonacci(n):\n    return n"
    assert language_detector.detect_language("code.txt", py_code) == "python"

    java_code = "public class Hello {\n  public static void main(String[] args) {\n    System.out.println(\"Hi\");\n  }\n}"
    assert language_detector.detect_language("code.txt", java_code) == "java"

    cpp_code = "#include <iostream>\nusing namespace std;\nint main() { cout << 1; }"
    assert language_detector.detect_language("header.h", cpp_code) == "cpp"


def test_submission_ast_parse_endpoint(client, test_student, test_instructor):
    # Setup Course & Assignment
    inst_login = client.post("/api/v1/auth/login", data={"username": "prof_miller", "password": "securepass123"})
    inst_token = inst_login.json()["access_token"]
    
    course_res = client.post(
        "/api/v1/courses/",
        json={"code": "CS600", "title": "Compiler Construction"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    course_id = course_res.json()["id"]

    assign_res = client.post(
        f"/api/v1/assignments/course/{course_id}",
        json={"title": "Parser Lab", "language": "python"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assign_id = assign_res.json()["id"]

    # Student Login & Submission
    std_login = client.post("/api/v1/auth/login", data={"username": "alex_student", "password": "studentpass123"})
    std_token = std_login.json()["access_token"]

    sub_res = client.post(
        f"/api/v1/submissions/assignment/{assign_id}",
        json={
            "files": [
                {
                    "filename": "solution.py",
                    "content": "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n",
                    "language": "python"
                }
            ]
        },
        headers={"Authorization": f"Bearer {std_token}"},
    )
    sub_id = sub_res.json()["id"]

    # Trigger AST Parse
    parse_res = client.post(
        f"/api/v1/submissions/{sub_id}/parse",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert parse_res.status_code == 200
    ast_nodes = parse_res.json()
    assert len(ast_nodes) > 0
    node_types = [n["node_type"] for n in ast_nodes]
    assert "function_definition" in node_types

    # Query AST nodes via GET endpoint
    get_ast_res = client.get(
        f"/api/v1/submissions/{sub_id}/ast",
        headers={"Authorization": f"Bearer {std_token}"},
    )
    assert get_ast_res.status_code == 200
    retrieved_nodes = get_ast_res.json()
    assert len(retrieved_nodes) == len(ast_nodes)
