"""
快速验证脚本 - 检查整合是否成功
"""

import sys
import os

def check_module_structure():
    """检查模块结构"""
    print("🔍 检查模块结构...")

    required_files = [
        'app/services/auto_apply/__init__.py',
        'app/services/auto_apply/base_applier.py',
        'app/services/auto_apply/linkedin_applier.py',
        'app/services/auto_apply/config.py',
        'app/services/auto_apply/question_handler.py',
        'app/services/auto_apply/session_manager.py',
    ]

    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
            print(f"  ✗ 缺失: {file}")
        else:
            print(f"  ✓ 存在: {file}")

    return len(missing) == 0


def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")

    required_packages = [
        'selenium',
        'undetected_chromedriver',
        'webdriver_manager'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ 已安装: {package}")
        except ImportError:
            missing.append(package)
            print(f"  ✗ 未安装: {package}")

    return len(missing) == 0


def check_imports():
    """检查模块导入"""
    print("\n🔍 检查模块导入...")

    try:
        from app.services.auto_apply import BaseApplier, LinkedInApplier
        print("  ✓ BaseApplier 导入成功")
        print("  ✓ LinkedInApplier 导入成功")

        from app.services.auto_apply.config import AutoApplyConfig, validate_config
        print("  ✓ AutoApplyConfig 导入成功")

        from app.services.auto_apply.question_handler import QuestionHandler
        print("  ✓ QuestionHandler 导入成功")

        from app.services.auto_apply.session_manager import SessionManager
        print("  ✓ SessionManager 导入成功")

        return True

    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        return False


def check_config():
    """检查配置"""
    print("\n🔍 检查配置...")

    try:
        from app.services.auto_apply.config import AutoApplyConfig, validate_config

        # 测试默认配置
        config = AutoApplyConfig()
        print(f"  ✓ 默认配置创建成功")

        # 测试配置验证
        config.keywords = "Python Developer"
        is_valid, error = validate_config(config)

        if is_valid:
            print(f"  ✓ 配置验证通过")
        else:
            print(f"  ✗ 配置验证失败: {error}")
            return False

        return True

    except Exception as e:
        print(f"  ✗ 配置检查失败: {e}")
        return False


def check_api_endpoints():
    """检查 API 接口"""
    print("\n🔍 检查 API 接口...")

    try:
        with open('web_app.py', 'r', encoding='utf-8') as f:
            content = f.read()

        endpoints = [
            '/api/auto-apply/start',
            '/api/auto-apply/stop',
            '/api/auto-apply/status',
            '/api/auto-apply/history',
            '/ws/auto-apply/'
        ]

        all_found = True
        for endpoint in endpoints:
            if endpoint in content:
                print(f"  ✓ 接口存在: {endpoint}")
            else:
                print(f"  ✗ 接口缺失: {endpoint}")
                all_found = False

        return all_found

    except Exception as e:
        print(f"  ✗ API 检查失败: {e}")
        return False


def check_frontend():
    """检查前端文件"""
    print("\n🔍 检查前端文件...")

    if os.path.exists('static/auto_apply_panel.html'):
        print("  ✓ 控制面板存在: static/auto_apply_panel.html")

        # 检查文件大小
        size = os.path.getsize('static/auto_apply_panel.html')
        print(f"  ✓ 文件大小: {size} 字节")

        return True
    else:
        print("  ✗ 控制面板缺失")
        return False


def check_tests():
    """检查测试文件"""
    print("\n🔍 检查测试文件...")

    if os.path.exists('tests/test_auto_apply.py'):
        print("  ✓ 测试文件存在: tests/test_auto_apply.py")

        # 统计测试用例数量
        with open('tests/test_auto_apply.py', 'r', encoding='utf-8') as f:
            content = f.read()
            test_count = content.count('def test_')
            print(f"  ✓ 测试用例数量: {test_count}")

        return True
    else:
        print("  ✗ 测试文件缺失")
        return False


def check_documentation():
    """检查文档"""
    print("\n🔍 检查文档...")

    docs = [
        'docs/auto_apply_guide.md',
        '整合方案_GitHub高星投简历应用.md',
        '整合完成报告.md'
    ]

    all_found = True
    for doc in docs:
        if os.path.exists(doc):
            print(f"  ✓ 文档存在: {doc}")
        else:
            print(f"  ✗ 文档缺失: {doc}")
            all_found = False

    return all_found


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI求职助手 - 自动投递功能验证")
    print("=" * 60)

    results = {
        '模块结构': check_module_structure(),
        '依赖包': check_dependencies(),
        '模块导入': check_imports(),
        '配置管理': check_config(),
        'API接口': check_api_endpoints(),
        '前端文件': check_frontend(),
        '测试文件': check_tests(),
        '文档': check_documentation()
    }

    print("\n" + "=" * 60)
    print("📊 验证结果汇总")
    print("=" * 60)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:12} {status}")

    total = len(results)
    passed = sum(results.values())
    percentage = (passed / total) * 100

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 通过 ({percentage:.1f}%)")
    print("=" * 60)

    if passed == total:
        print("\n🎉 恭喜！所有检查都通过了！")
        print("✅ 自动投递功能已成功整合")
        print("\n下一步:")
        print("1. 运行测试: pytest tests/test_auto_apply.py -v")
        print("2. 启动服务: python web_app.py")
        print("3. 访问面板: http://localhost:8000/static/auto_apply_panel.html")
        return 0
    else:
        print("\n⚠️ 部分检查未通过，请查看上面的详细信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())
