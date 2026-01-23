from app import create_app, db
from database.models import User
import os

app = create_app()

with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@hospital.com').first()
        if not admin:
            admin = User(
                full_name='System Administrator',
                email='admin@hospital.com'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created:")
            print("   Email: admin@hospital.com")
            print("   Password: admin123")
        else:
            print("✅ Admin user already exists")
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        print("Try deleting the endometriosis.db file and restarting the application")

if __name__ == "__main__":
    app.run(debug=True)