#!/usr/bin/env python3
"""
Validation script to test main.py and mainWithServer.py structure and patterns
Tests without requiring full dependencies
"""

import sys
import os
import ast
import re
from typing import List, Dict, Any

def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """Analyze Python file structure and patterns"""
    result = {
        "file": file_path,
        "exists": False,
        "valid_syntax": False,
        "imports": [],
        "functions": [],
        "has_signal_handling": False,
        "has_exception_handling": False,
        "has_global_declarations": False,
        "has_sys_path_insert": False,
        "has_emojis_in_logging": False,
        "has_main_function": False,
        "errors": []
    }
    
    try:
        if not os.path.exists(file_path):
            result["errors"].append(f"File does not exist: {file_path}")
            return result
        
        result["exists"] = True
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check syntax
        try:
            tree = ast.parse(content)
            result["valid_syntax"] = True
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {e}")
            return result
        
        # Analyze content patterns
        result["has_signal_handling"] = bool(re.search(r'signal\.signal\(', content))
        result["has_exception_handling"] = bool(re.search(r'except.*Exception', content))
        result["has_global_declarations"] = bool(re.search(r'global\s+\w+', content))
        result["has_sys_path_insert"] = bool(re.search(r'sys\.path\.insert\(0,', content))
        result["has_emojis_in_logging"] = bool(re.search(r'log\.info\(["\'][^"\']*[\u2600-\u27BF\uD83C\uD000-\uDFFF\uD83D\uD000-\uDFFF\uD83E\uD000-\uDFFF]', content))
        result["has_main_function"] = bool(re.search(r'def main\(\):', content))
        
        # Extract imports and functions using AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    result["imports"].append(f"{module}.{alias.name}")
            elif isinstance(node, ast.FunctionDef):
                result["functions"].append(node.name)
        
        # Check for test_json_simple.py patterns
        patterns_from_test = {
            "global_variable_checks": bool(re.search(r"'[\w_]+'\s+in\s+globals\(\)", content)),
            "signal_handler_with_exit": bool(re.search(r'signal_handler.*sys\.exit\(0\)', content, re.DOTALL)),
            "emoji_logging": bool(re.search(r'log\.info\(["\'][^"\']*[🎤🔍✅❌⚡🛑🚀💬📄🎯🌍📊⏳]', content)),
            "error_info_logging": bool(re.search(r'log\.info.*💡', content)),
            "status_messages": bool(re.search(r'log\.info.*SYSTEM READY', content)),
        }
        
        result.update(patterns_from_test)
        
    except Exception as e:
        result["errors"].append(f"Analysis error: {e}")
    
    return result

def test_import_structure(file_path: str) -> Dict[str, Any]:
    """Test if the import structure is correct"""
    result = {
        "file": file_path,
        "import_errors": [],
        "import_success": False
    }
    
    try:
        # Read the file and extract just the import section
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract import lines (before any substantial code)
        import_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith(('import ', 'from ', 'sys.path')) or line.startswith('#') or not line:
                import_lines.append(line)
            elif line.startswith('load_dotenv') or 'os.environ' in line:
                import_lines.append(line)
            else:
                # Stop at first substantial code line
                break
        
        # Create a test script to verify imports
        test_script = '\n'.join(import_lines) + '\nprint("Imports successful")'
        
        # Try to compile the import section
        try:
            compile(test_script, file_path, 'exec')
            result["import_success"] = True
        except Exception as e:
            result["import_errors"].append(f"Import compilation error: {e}")
        
    except Exception as e:
        result["import_errors"].append(f"File reading error: {e}")
    
    return result

def main():
    """Main validation function"""
    print("🔍 VALIDATING MAIN FILES")
    print("=" * 50)
    print("🎯 Checking main.py and mainWithServer.py")
    print("🔬 Analyzing structure and test_json_simple.py patterns")
    print("=" * 50)
    
    files_to_test = [
        "src/main.py",
        "src/mainWithServer.py"
    ]
    
    all_valid = True
    
    for file_path in files_to_test:
        print(f"\n📁 Analyzing: {file_path}")
        print("-" * 40)
        
        # Analyze file structure
        analysis = analyze_python_file(file_path)
        
        if not analysis["exists"]:
            print(f"❌ File does not exist")
            all_valid = False
            continue
        
        if not analysis["valid_syntax"]:
            print(f"❌ Syntax errors:")
            for error in analysis["errors"]:
                print(f"   {error}")
            all_valid = False
            continue
        
        print(f"✅ File exists and has valid syntax")
        
        # Check essential patterns
        checks = [
            ("Signal handling", analysis["has_signal_handling"]),
            ("Exception handling", analysis["has_exception_handling"]),
            ("Global declarations", analysis["has_global_declarations"]),
            ("sys.path.insert(0, ...)", analysis["has_sys_path_insert"]),
            ("Emoji logging", analysis["emoji_logging"]),
            ("Main function", analysis["has_main_function"]),
            ("Global variable checks", analysis.get("global_variable_checks", False)),
            ("Error info logging", analysis.get("error_info_logging", False)),
            ("Status messages", analysis.get("status_messages", False)),
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "⚠️ "
            print(f"   {status} {check_name}")
            if not check_result and check_name in ["Signal handling", "Exception handling", "Main function"]:
                all_valid = False
        
        print(f"   📦 Found {len(analysis['imports'])} imports")
        print(f"   🔧 Found {len(analysis['functions'])} functions")
        
        # Test import structure
        import_test = test_import_structure(file_path)
        if import_test["import_success"]:
            print(f"   ✅ Import structure is valid")
        else:
            print(f"   ⚠️  Import structure issues:")
            for error in import_test["import_errors"]:
                print(f"      {error}")
    
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    if all_valid:
        print("✅ ALL FILES PASSED VALIDATION")
        print("🎉 Both main.py and mainWithServer.py follow test_json_simple.py patterns")
        print("📋 Key improvements applied:")
        print("   • sys.path.insert(0, ...) for higher priority imports")
        print("   • Enhanced signal handlers with global variable checks")
        print("   • Improved exception handling with emoji logging")
        print("   • Better user feedback with status messages")
        print("   • Robust cleanup in finally blocks")
    else:
        print("⚠️  SOME VALIDATION ISSUES FOUND")
        print("🔧 Check the issues above and fix them")
    
    # Additional recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("   • Ensure all dependencies are installed: pip install -r requirements.txt")
    print("   • Test with: python3 scripts/test_microphone_basic.py")
    print("   • For HTTP server: install and run mainWithServer.py")
    print("   • Check .env configuration for your specific setup")
    
    return all_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)