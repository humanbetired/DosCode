# Code Review Checklist

## Before Approving Any PR

### Functionality
- [ ] Code does what the PR description says
- [ ] Edge cases are handled
- [ ] No obvious logic errors

### Code Quality
- [ ] No functions longer than 20 lines
- [ ] No parameters more than 4 per function  
- [ ] Complexity grade A or B (radon score < 10)
- [ ] No unused imports or variables

### Security (use bandit scan)
- [ ] No hardcoded credentials
- [ ] No dangerous functions (eval, exec)
- [ ] External inputs are validated

### Style
- [ ] Naming follows team conventions (PascalCase classes, snake_case functions)
- [ ] Docstrings present on public functions
- [ ] No wildcard imports

## Auto-Reject Criteria
Any PR with the following is automatically rejected:
1. Hardcoded API key or password
2. eval() with external input
3. Complexity grade D, E, or F
4. More than 20 lint errors