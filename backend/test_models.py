from app.database.base import Base
import app.models

print("Registered tables:")
print(Base.metadata.tables.keys())