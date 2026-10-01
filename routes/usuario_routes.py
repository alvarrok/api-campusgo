from flask import Blueprint
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)
from services.usuario_service import UsuarioService
from utils.response import success_response, error_response

usuario_bp = Blueprint("usuarios", __name__)

@usuario_bp.route("/api/perfil", methods=["GET"])
@jwt_required()
def obtener_perfil():
    usuario_id = get_jwt_identity()
    service = UsuarioService()
    data, message, http_code = service.obtener_perfil(usuario_id)

    if data is None:
        return error_response(message, http_code)

    return success_response(
        data,
        message,
        http_code
    )