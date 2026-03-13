"""
Central place to instantiate Flask extensions so circular imports are avoided.
"""
from flask_jwt_extended import JWTManager
from flask_mail import Mail

jwt = JWTManager()
mail = Mail()
