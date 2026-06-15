from backend.database import engine

with engine.connect() as conn:
    print("CONNECTED TO HAVILAH")
