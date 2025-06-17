from db.database import engine
import models

print("📁 Using DB at:", engine.url.database)

models.Base.metadata.create_all(bind=engine)
print("✅ Tables created.")
