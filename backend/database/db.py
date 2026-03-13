from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Initialize database with the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from models import user, branch, supplier, medicine, inventory, sales, prescription
        db.create_all()
        _seed_default_data()

    return db


def _seed_default_data():
    """Seed default admin user and branch if not present."""
    from models.user import User
    from models.branch import Branch

    # Create default branch
    if not Branch.query.first():
        branch = Branch(
            name="Main Branch",
            address="123 Main Street",
            phone="0000000000",
            email="main@pharmacy.com",
            is_active=True,
        )
        db.session.add(branch)
        db.session.flush()

        # Create default admin
        if not User.query.filter_by(email="admin@pharmacy.com").first():
            admin = User(
                full_name="System Admin",
                email="admin@pharmacy.com",
                role="admin",
                branch_id=branch.id,
                is_active=True,
            )
            admin.set_password("Admin@1234")
            db.session.add(admin)

        db.session.commit()
