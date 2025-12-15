"""
Code Validation Engine - Static + Runtime Checks
Validates code correctness with sandbox execution
"""
import ast
import re
import subprocess
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of code validation"""
    passed: bool
    test_results: List[Dict]
    syntax_valid: bool
    complexity_warnings: List[str]
    execution_time: float
    memory_estimate: str
    error_message: Optional[str] = None
    counterexamples: List[Dict] = None


class CodeValidator:
    """
    Validates code with static analysis and runtime testing
    Supports Python, JavaScript, Java
    """
    
    def __init__(self, language: str = "python"):
        self.language = language.lower()
        self.max_execution_time = 5  # seconds
        
    def validate(self, code: str, test_cases: List[Dict]) -> ValidationResult:
        """
        Full validation: static checks + runtime tests
        
        Args:
            code: Source code to validate
            test_cases: List of {"input": ..., "expected": ...}
        
        Returns:
            ValidationResult with all checks
        """
        # Static checks
        syntax_valid, syntax_error = self._check_syntax(code)
        if not syntax_valid:
            return ValidationResult(
                passed=False,
                test_results=[],
                syntax_valid=False,
                complexity_warnings=[],
                execution_time=0,
                memory_estimate="N/A",
                error_message=syntax_error
            )
        
        complexity_warnings = self._check_complexity(code)
        
        # Runtime tests
        if self.language == "python":
            test_results, exec_time = self._run_python_tests(code, test_cases)
        elif self.language == "javascript":
            test_results, exec_time = self._run_js_tests(code, test_cases)
        elif self.language == "java":
            test_results, exec_time = self._run_java_tests(code, test_cases)
        else:
            return ValidationResult(
                passed=False,
                test_results=[],
                syntax_valid=True,
                complexity_warnings=[],
                execution_time=0,
                memory_estimate="N/A",
                error_message=f"Language {self.language} not supported"
            )
        
        # Check if all tests passed
        all_passed = all(t["passed"] for t in test_results)
        
        # Find counterexamples
        counterexamples = [
            {
                "input": t["input"],
                "expected": t["expected"],
                "actual": t.get("actual")
            }
            for t in test_results if not t["passed"]
        ]
        
        return ValidationResult(
            passed=all_passed,
            test_results=test_results,
            syntax_valid=True,
            complexity_warnings=complexity_warnings,
            execution_time=exec_time,
            memory_estimate=self._estimate_memory(code),
            counterexamples=counterexamples if counterexamples else None
        )
    
    def _check_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Check syntax validity"""
        try:
            if self.language == "python":
                ast.parse(code)
            elif self.language == "javascript":
                # Basic check - try to run through Node
                result = subprocess.run(
                    ["node", "--check"],
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode != 0:
                    return False, result.stderr
            # For Java, compile check happens in runtime
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
    
    def _check_complexity(self, code: str) -> List[str]:
        """Detect complexity issues"""
        warnings = []
        
        if self.language == "python":
            # Detect nested loops (potential O(n²) or worse)
            nested_loops = code.count("for ") + code.count("while ")
            if nested_loops >= 3:
                warnings.append("⚠ Multiple nested loops detected - consider O(n²) or O(n³) complexity")
            
            # Detect recursive calls
            if "def " in code and code.count("return") > 1:
                func_names = re.findall(r'def (\w+)\(', code)
                for func in func_names:
                    if code.count(f"{func}(") > 1:
                        warnings.append(f"⚠ Recursive function '{func}' detected - ensure base case exists")
            
            # Detect common inefficiencies
            if ".append(" in code and "for " in code:
                warnings.append("💡 List append in loop - consider list comprehension")
            
            if "sorted(" in code or ".sort(" in code:
                warnings.append("💡 Sort detected - time complexity at least O(n log n)")
        
        return warnings
    
    def _run_python_tests(self, code: str, test_cases: List[Dict]) -> Tuple[List[Dict], float]:
        """Run Python code in sandbox with test cases"""
        results = []
        total_time = 0
        
        for i, test in enumerate(test_cases):
            try:
                # Create sandbox environment
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    # Extract function name
                    func_match = re.search(r'def (\w+)\(', code)
                    func_name = func_match.group(1) if func_match else "solution"
                    
                    # Write test harness
                    test_code = f"""
import time
import json
import sys

{code}

# Test case
test_input = {json.dumps(test['input'])}
expected = {json.dumps(test['expected'])}

try:
    start = time.time()
    if isinstance(test_input, dict):
        result = {func_name}(**test_input)
    elif isinstance(test_input, list):
        result = {func_name}(*test_input)
    else:
        result = {func_name}(test_input)
    elapsed = time.time() - start
    
    passed = result == expected
    print(json.dumps({{
        "passed": passed,
        "actual": result,
        "time": elapsed
    }}))
except Exception as e:
    print(json.dumps({{
        "passed": False,
        "error": str(e),
        "time": 0
    }}))
"""
                    f.write(test_code)
                    f.flush()
                    
                    # Run in subprocess (sandboxed)
                    result = subprocess.run(
                        ["python", f.name],
                        capture_output=True,
                        text=True,
                        timeout=self.max_execution_time
                    )
                    
                    # Parse result
                    output = json.loads(result.stdout.strip())
                    results.append({
                        "test_num": i + 1,
                        "passed": output["passed"],
                        "input": test["input"],
                        "expected": test["expected"],
                        "actual": output.get("actual"),
                        "error": output.get("error")
                    })
                    total_time += output.get("time", 0)
                    
            except subprocess.TimeoutExpired:
                results.append({
                    "test_num": i + 1,
                    "passed": False,
                    "input": test["input"],
                    "expected": test["expected"],
                    "error": f"Timeout: exceeded {self.max_execution_time}s"
                })
            except Exception as e:
                results.append({
                    "test_num": i + 1,
                    "passed": False,
                    "input": test["input"],
                    "expected": test["expected"],
                    "error": str(e)
                })
            finally:
                # Cleanup
                try:
                    os.unlink(f.name)
                except:
                    pass
        
        return results, total_time
    
    def _run_js_tests(self, code: str, test_cases: List[Dict]) -> Tuple[List[Dict], float]:
        """Run JavaScript code with Node.js"""
        results = []
        total_time = 0
        
        for i, test in enumerate(test_cases):
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                    # Extract function name
                    func_match = re.search(r'function (\w+)\(', code)
                    func_name = func_match.group(1) if func_match else "solution"
                    
                    test_code = f"""
{code}

const testInput = {json.dumps(test['input'])};
const expected = {json.dumps(test['expected'])};

try {{
    const start = Date.now();
    const result = {func_name}(testInput);
    const elapsed = (Date.now() - start) / 1000;
    
    const passed = JSON.stringify(result) === JSON.stringify(expected);
    console.log(JSON.stringify({{
        passed: passed,
        actual: result,
        time: elapsed
    }}));
}} catch (e) {{
    console.log(JSON.stringify({{
        passed: false,
        error: e.message,
        time: 0
    }}));
}}
"""
                    f.write(test_code)
                    f.flush()
                    
                    result = subprocess.run(
                        ["node", f.name],
                        capture_output=True,
                        text=True,
                        timeout=self.max_execution_time
                    )
                    
                    output = json.loads(result.stdout.strip())
                    results.append({
                        "test_num": i + 1,
                        "passed": output["passed"],
                        "input": test["input"],
                        "expected": test["expected"],
                        "actual": output.get("actual"),
                        "error": output.get("error")
                    })
                    total_time += output.get("time", 0)
                    
            except Exception as e:
                results.append({
                    "test_num": i + 1,
                    "passed": False,
                    "input": test["input"],
                    "expected": test["expected"],
                    "error": str(e)
                })
            finally:
                try:
                    os.unlink(f.name)
                except:
                    pass
        
        return results, total_time
    
    def _run_java_tests(self, code: str, test_cases: List[Dict]) -> Tuple[List[Dict], float]:
        """Run Java code with compilation + execution"""
        # Simplified - full implementation would need proper Java harness
        results = []
        for i, test in enumerate(test_cases):
            results.append({
                "test_num": i + 1,
                "passed": False,
                "input": test["input"],
                "expected": test["expected"],
                "error": "Java validation not fully implemented yet"
            })
        return results, 0
    
    def _estimate_memory(self, code: str) -> str:
        """Rough memory estimation"""
        # Count data structures
        lists = code.count("[") + code.count("list(") + code.count("List")
        dicts = code.count("{") + code.count("dict(") + code.count("Dict")
        sets = code.count("set(") + code.count("Set")
        
        if lists + dicts + sets > 5:
            return "High (multiple data structures)"
        elif lists + dicts + sets > 2:
            return "Medium (few data structures)"
        else:
            return "Low (minimal storage)"


def validate_code(code: str, language: str, test_cases: List[Dict]) -> ValidationResult:
    """
    Convenience function to validate code
    
    Example:
        result = validate_code(
            code='def two_sum(nums, target): ...',
            language='python',
            test_cases=[
                {"input": [[2,7,11,15], 9], "expected": [0,1]},
                {"input": [[3,2,4], 6], "expected": [1,2]}
            ]
        )
    """
    validator = CodeValidator(language)
    return validator.validate(code, test_cases)
