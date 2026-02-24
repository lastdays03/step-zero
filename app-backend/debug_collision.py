import sys
import os
from sqlmodel import SQLModel

# Add both /app and /app/app to sys.path to simulate potential issues
sys.path.append("/app")
sys.path.append("/app/app")

print("--- SQLModel Metadata Debug ---")

def dump_metadata():
    print(f"\nCurrent tables in SQLModel.metadata ({hex(id(SQLModel.metadata))}):")
    for table in SQLModel.metadata.tables:
        print(f" - {table}")

try:
    print("\nImporting 'app.models'...")
    import app.models
    dump_metadata()
except Exception as e:
    print(f"Error importing app.models: {e}")

try:
    # This might conflict if PYTHONPATH is set to /app but we also have app/ folder
    print("\nImporting 'models' directly if possible...")
    import models
    dump_metadata()
except Exception as e:
    print(f"Could not import 'models' directly: {e}")

print("\nChecking for duplicated tablenames...")
tables = list(SQLModel.metadata.tables.keys())
if len(tables) != len(set(tables)):
    print("WARNING: Duplicate table names found in metadata!")
else:
    print("No immediate duplicate names in current metadata object.")
