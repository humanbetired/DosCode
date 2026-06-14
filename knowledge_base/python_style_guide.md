# Python Coding Standards — ReviewAgent Team

## 1. Naming Conventions
- Classes: PascalCase (e.g., `MyClass`, `DataProcessor`)
- Functions and methods: snake_case (e.g., `process_data`, `get_user`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `API_BASE_URL`)
- Variables: snake_case, descriptive names (avoid `x`, `val`, `tmp`)
- Private methods: prefix with underscore (e.g., `_internal_method`)

## 2. Function Design
- Maximum function length: 20 lines
- Maximum parameters: 4 parameters per function
- Each function should do ONE thing only (Single Responsibility)
- Avoid deeply nested conditions (max 3 levels)
- Always add docstring for public functions

## 3. Security Rules
- NEVER hardcode credentials, API keys, or passwords in source code
- Use environment variables or secrets manager instead
- Never use `eval()` or `exec()` with user-supplied input
- Always validate and sanitize external inputs
- Use parameterized queries for database operations

## 4. Import Rules
- Remove all unused imports
- Standard library imports first, then third-party, then local
- Never use wildcard imports (`from module import *`)
- One import per line

## 5. Code Complexity
- Cyclomatic complexity must stay below 10 per function (grade A or B)
- If complexity exceeds 10, refactor into smaller functions
- Avoid more than 3 levels of nesting — extract to helper functions

## 6. Error Handling
- Always use specific exception types (avoid bare `except:`)
- Log errors with context, not just `print()`
- Never silently swallow exceptions

## 7. Documentation
- All public classes and functions must have docstrings
- Docstring format: Google style
- Complex logic must have inline comments