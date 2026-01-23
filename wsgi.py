import os
from app import create_app, db
from database.models import User

app = create_app()

# Initialize database on startup
with app.app_context():
    try:
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

if __name__ == "__main__":
    app.run()
