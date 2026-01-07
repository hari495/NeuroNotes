# Python Best Practices and Tips

## Code Style and Formatting

### PEP 8 Guidelines
- Use 4 spaces for indentation (not tabs)
- Limit lines to 79 characters for code, 72 for comments
- Use snake_case for functions and variables
- Use PascalCase for class names
- Use UPPER_CASE for constants

### Naming Conventions
```python
# Good
user_name = "John"
def calculate_total_price(items):
    pass

class UserProfile:
    pass

MAX_CONNECTIONS = 100
```

## Testing Best Practices

### Unit Testing with pytest
- Write tests for all critical functions
- Use descriptive test names (test_should_return_zero_when_input_is_empty)
- Aim for at least 80% code coverage
- Use fixtures for common setup code
- Mock external dependencies

### Example Test
```python
import pytest

def test_add_function():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
```

## Performance Optimization

### Profiling Before Optimizing
- Use cProfile or line_profiler to identify bottlenecks
- Don't optimize prematurely
- Focus on algorithmic improvements first

### Common Optimizations
1. Use built-in functions (they're implemented in C)
2. List comprehensions are faster than loops
3. Use generators for large datasets
4. Cache expensive function calls with @lru_cache
5. Use sets for membership testing instead of lists

### Example: List Comprehension
```python
# Slower
squares = []
for i in range(1000):
    squares.append(i ** 2)

# Faster
squares = [i ** 2 for i in range(1000)]
```

## Error Handling

### Use Specific Exceptions
```python
# Good
try:
    result = risky_operation()
except ValueError as e:
    handle_value_error(e)
except FileNotFoundError as e:
    handle_missing_file(e)
```

### Context Managers
Use `with` statements for resource management:
```python
with open('file.txt', 'r') as f:
    content = f.read()
```

## Type Hints

Add type hints for better code documentation:
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def process_items(items: list[int]) -> dict[str, int]:
    return {"total": sum(items), "count": len(items)}
```

## Async Programming

Use async/await for I/O-bound operations:
```python
import asyncio
import aiohttp

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## Virtual Environments

Always use virtual environments:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Documentation

### Docstrings
Use Google or NumPy style docstrings:
```python
def calculate_area(length: float, width: float) -> float:
    """
    Calculate the area of a rectangle.

    Args:
        length: The length of the rectangle.
        width: The width of the rectangle.

    Returns:
        The area of the rectangle.

    Raises:
        ValueError: If length or width is negative.
    """
    if length < 0 or width < 0:
        raise ValueError("Dimensions must be positive")
    return length * width
```

## Security Best Practices

1. Never hardcode credentials
2. Use environment variables for sensitive data
3. Validate and sanitize user input
4. Use parameterized queries to prevent SQL injection
5. Keep dependencies updated
6. Use tools like bandit for security scanning

## Useful Tools

- **Black**: Automatic code formatting
- **Ruff**: Fast Python linter
- **mypy**: Static type checker
- **pytest**: Testing framework
- **pre-commit**: Git hooks for code quality
