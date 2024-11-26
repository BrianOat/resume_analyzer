# Coding Standards for Python Backend and React Frontend

## General Coding Principles
- Ensure consistency across the codebase.
- Follow industry-standard practices for readability and maintainability.
- Keep code modular and reusable.

---

## Python Backend Standards (FastAPI or similar)

### Naming Conventions
- **Variables and Functions**: Use `snake_case` (e.g., `process_data`, `user_id`).
- **Classes**: Use `PascalCase` (e.g., `DataProcessor`, `UserProfile`).
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `MAX_CONNECTIONS`, `API_KEY`).

### Spacing and Indentation
- Use **1 tab** for indentation.
- Leave **1 blank line** between functions and **2 blank lines** between classes.
- Limit line length to **79 characters** (PEP 8 standard).

### Commenting
- Use **docstrings** for all public classes and functions.
  ```python
  def fetch_data(api_url: str) -> dict:
      """
      Fetch data from the given API URL.
      
      Args:
          api_url (str): The URL of the API to fetch data from.
      
      Returns:
          dict: The JSON response parsed into a dictionary.
      """
  ```
- Use single-line comments (`#`) sparingly for inline explanations.

### Best Practices
- Use **type hints** for functions and method arguments.
- Keep functions concise; if a function exceeds 50 lines, consider refactoring.
- Import modules at the top of the file in logical order:
  - Standard library imports.
  - Third-party imports.
  - Local application imports.
- Example:
  ```python
  import os
  import sys
  from fastapi import FastAPI
  from .utils import process_data
  ```

---

## React Frontend Standards (JavaScript/TypeScript)

### Naming Conventions
- **Variables and Functions**: Use `camelCase` (e.g., `fetchData`, `userProfile`).
- **Components**: Use `PascalCase` (e.g., `UserProfile`, `NavBar`).
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `MAX_RESULTS`, `API_ENDPOINT`).

### Spacing and Indentation
- Use **1 tab** for indentation.
- Leave **1 blank line** between component methods.

### Commenting
- Use **JSDoc** for function and method documentation:
  ```javascript
  /**
   * Fetch user data from the API.
   * @param {string} userId - The ID of the user.
   * @returns {Promise<object>} - The user data as a promise.
   */
  async function fetchUserData(userId) {
      // Implementation
  }
  ```
- Use `//` for single-line comments within JSX/JavaScript.

### JSX and Formatting
- Always use **self-closing tags** when there are no children (e.g., `<Input />`).
- Prefer **functional components** over class components.
- Ensure components are concise; split larger ones into smaller subcomponents.

### Best Practices
- Organize imports:
  - React imports (e.g., `import React from 'react';`).
  - Third-party library imports.
  - Local imports (e.g., `import { UserCard } from './components/UserCard';`).
- Use **PropTypes** or **TypeScript** for type-checking.
- Avoid inline styles; use **CSS modules** or **styled-components** for styling.

---