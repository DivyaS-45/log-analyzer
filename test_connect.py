from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://postgres:postgres123@localhost/log_analyzer"
)

with engine.connect() as conn:
    print("Connected Successfully")
