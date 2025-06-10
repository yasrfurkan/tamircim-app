from tamircim import tamircim, db
with tamircim.app_context():
    db.create_all()