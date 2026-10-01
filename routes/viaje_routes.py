from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.viaje_service import ViajeService
from utils.response import success_response, error_response

viaje_bp = Blueprint("viajes", __name__)

@viaje_bp.route("/api/viajes", methods=["POST"])
@jwt_required()
def crear_viaje():
    claims = get_jwt()
    
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)
        
    datos = request.get_json(silent=True) or {}
    service = ViajeService()
    data, message, code = service.crear(
        get_jwt_identity(),
        datos
    )
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes", methods=["GET"])
@jwt_required()
def listar_viajes():
    filtros = {
        "origen": request.args.get("origen"),
        "destino": request.args.get("destino"),
        "fecha": request.args.get("fecha"),
        "estado": request.args.get("estado"),
        "precio_min": request.args.get("precio_min"),
        "precio_max": request.args.get("precio_max"),
        "solo_disponibles": request.args.get("solo_disponibles", type=lambda v: str(v).lower() == 'true'),
        "desde": request.args.get("desde")
    }
    
    data, message, code = ViajeService().listar(filtros)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/mios", methods=["GET"])
@jwt_required()
def listar_mis_viajes():
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)
        
    data, message, code = ViajeService().listar_mis_viajes(get_jwt_identity())
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/resumen", methods=["GET"])
@jwt_required()
def resumen_viajes():
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)
        
    data, message, code = ViajeService().resumen_viajes(get_jwt_identity())
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)

@viaje_bp.route("/api/viajes/<int:viaje_id>", methods=["GET"])
@jwt_required()
def obtener_viaje(viaje_id):
    data, message, code = ViajeService().obtener(viaje_id)
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>", methods=["PUT"])
@jwt_required()
def actualizar_viaje(viaje_id):
    datos = request.get_json(silent=True) or {}
    
    data, message, code = ViajeService().actualizar(
        get_jwt_identity(),
        viaje_id,
        datos
    )
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>", methods=["DELETE"])
@jwt_required()
def cancelar_viaje(viaje_id):
    data, message, code = ViajeService().cancelar(
        get_jwt_identity(),
        viaje_id
    )
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>/cupos", methods=["PATCH"])
@jwt_required()
def actualizar_cupos_viaje(viaje_id):
    datos = request.get_json(silent=True) or {}
    
    data, message, code = ViajeService().actualizar_cupos(
        get_jwt_identity(),
        viaje_id,
        datos
    )
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>/estado", methods=["PATCH"])
@jwt_required()
def cambiar_estado_viaje(viaje_id):
    datos = request.get_json(silent=True) or {}
    
    data, message, code = ViajeService().cambiar_estado(
        get_jwt_identity(),
        viaje_id,
        datos
    )
    
    if data is None:
        return error_response(message, code)
        
    return success_response(data, message, code)

