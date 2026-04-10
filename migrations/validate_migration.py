#!/usr/bin/env python3
"""
Validation script for SQL migration files.

This script performs basic validation on SQL migration files without
executing them against a database. It checks for:
- File existence and readability
- Basic SQL syntax patterns
- Required tables and indexes
- Foreign key constraints

Usage:
    python migrations/validate_migration.py [migration_file]
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def validate_sql_syntax(sql_content: str) -> List[str]:
    """
    Perform basic SQL syntax validation.
    
    Returns:
        List of validation warnings/errors
    """
    issues = []
    
    # Check for balanced parentheses
    if sql_content.count('(') != sql_content.count(')'):
        issues.append("Unbalanced parentheses detected")
    
    # Check for CREATE TABLE statements
    create_table_count = len(re.findall(r'CREATE TABLE', sql_content, re.IGNORECASE))
    if create_table_count == 0:
        issues.append("No CREATE TABLE statements found")
    
    # Check for semicolons at statement ends
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    if len(statements) == 0:
        issues.append("No SQL statements found")
    
    return issues


def extract_tables(sql_content: str) -> List[str]:
    """Extract table names from CREATE TABLE statements."""
    pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)'
    matches = re.findall(pattern, sql_content, re.IGNORECASE)
    return matches


def extract_indexes(sql_content: str) -> List[str]:
    """Extract index names from CREATE INDEX statements."""
    pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF NOT EXISTS\s+)?(\w+)'
    matches = re.findall(pattern, sql_content, re.IGNORECASE)
    return matches


def extract_foreign_keys(sql_content: str) -> List[Tuple[str, str]]:
    """Extract foreign key relationships."""
    pattern = r'REFERENCES\s+(\w+)\s*\((\w+)\)'
    matches = re.findall(pattern, sql_content, re.IGNORECASE)
    return matches


def validate_migration_001(sql_content: str) -> List[str]:
    """
    Validate specific requirements for migration 001.
    
    Expected tables:
    - calls
    - transcripts
    - leads
    - appointments
    - business_config
    - call_analytics
    - crm_sync_log
    """
    issues = []
    
    required_tables = [
        'calls',
        'transcripts',
        'leads',
        'appointments',
        'business_config',
        'call_analytics',
        'crm_sync_log'
    ]
    
    tables = extract_tables(sql_content)
    
    for required_table in required_tables:
        if required_table not in tables:
            issues.append(f"Missing required table: {required_table}")
    
    # Check for indexes
    indexes = extract_indexes(sql_content)
    if len(indexes) < 10:
        issues.append(f"Expected at least 10 indexes, found {len(indexes)}")
    
    # Check for foreign keys
    foreign_keys = extract_foreign_keys(sql_content)
    if len(foreign_keys) < 5:
        issues.append(f"Expected at least 5 foreign key constraints, found {len(foreign_keys)}")
    
    # Check for triggers
    if 'CREATE TRIGGER' not in sql_content:
        issues.append("No triggers found (expected updated_at triggers)")
    
    # Check for UUID extension
    if 'pgcrypto' not in sql_content.lower():
        issues.append("Missing pgcrypto extension for UUID support")
    
    return issues


def main():
    """Main validation entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_migration.py <migration_file>")
        print("\nExample:")
        print("  python migrations/validate_migration.py 001_initial_schema.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    
    # If relative path provided, resolve from migrations directory
    if not os.path.isabs(migration_file):
        migrations_dir = Path(__file__).parent
        migration_file = migrations_dir / migration_file
    else:
        migration_file = Path(migration_file)
    
    print("=" * 60)
    print("SQL Migration Validator")
    print("=" * 60)
    print(f"File: {migration_file}")
    print("=" * 60)
    print()
    
    # Check file exists
    if not migration_file.exists():
        print(f"✗ Error: File not found: {migration_file}")
        sys.exit(1)
    
    # Read file
    try:
        with open(migration_file, 'r') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)
    
    print(f"✓ File readable ({len(sql_content)} bytes)")
    
    # Basic syntax validation
    print("\nValidating SQL syntax...")
    syntax_issues = validate_sql_syntax(sql_content)
    
    if syntax_issues:
        print("✗ Syntax issues found:")
        for issue in syntax_issues:
            print(f"  - {issue}")
    else:
        print("✓ Basic syntax validation passed")
    
    # Extract and display tables
    print("\nTables found:")
    tables = extract_tables(sql_content)
    for table in tables:
        print(f"  - {table}")
    
    # Extract and display indexes
    print(f"\nIndexes found: {len(extract_indexes(sql_content))}")
    
    # Extract and display foreign keys
    print(f"Foreign keys found: {len(extract_foreign_keys(sql_content))}")
    
    # Migration-specific validation
    if '001_initial_schema' in str(migration_file):
        print("\nValidating migration 001 requirements...")
        migration_issues = validate_migration_001(sql_content)
        
        if migration_issues:
            print("✗ Migration validation issues:")
            for issue in migration_issues:
                print(f"  - {issue}")
        else:
            print("✓ Migration 001 validation passed")
    
    # Summary
    print("\n" + "=" * 60)
    all_issues = syntax_issues + (migration_issues if '001_initial_schema' in str(migration_file) else [])
    
    if all_issues:
        print(f"✗ Validation completed with {len(all_issues)} issue(s)")
        sys.exit(1)
    else:
        print("✓ All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    import os
    main()
