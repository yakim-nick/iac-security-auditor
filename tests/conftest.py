# Set fake credentials before any module imports Settings so the app can build
# API clients (Anthropic, GitHub) without real secrets during tests.
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
os.environ["GITHUB_TOKEN"] = "ghp_test"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
