from main import SessionLocal, Business

s = SessionLocal()
for b in s.query(Business).all():
    print(b.id, repr(b.name))
s.close()
