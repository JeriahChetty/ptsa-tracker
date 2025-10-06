from flask_login import current_user

def setup_template_helpers(app):
    """Register custom functions for use in Jinja2 templates."""

    @app.context_processor
    def utility_processor():
        def is_admin():
            return current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'

        def is_company():
            return current_user.is_authenticated and getattr(current_user, 'role', '') == 'company'
        
        # You can add other helpers here, like unread_notifications_count
        def unread_notifications_count():
            # Placeholder logic
            return 0

        return dict(
            is_admin=is_admin,
            is_company=is_company,
            unread_notifications_count=unread_notifications_count
        )
