from datetime import datetime
from database import get_connection
from repositories.reserva_repository import ReservaRepository

class ReservaService:

    def crear(self, usuario_id, datos):
        viajes = datos.get("viajes", [])

        if not isinstance(viajes, list) or len(viajes) not in (1, 2):
            return None, "Debe seleccionar uno o dos viajes", 400

        ids = [v.get("viaje_id") for v in viajes]

        if None in ids or len(ids) != len(set(ids)):
            return None, "Los viajes son inválidos o están repetidos", 400

        connection = get_connection()
        try:
            connection.begin()
            repository = ReservaRepository(connection)

            pasajero_id = repository.obtener_pasajero_id_por_usuario(usuario_id)
            if pasajero_id is None:
                connection.rollback()
                return None, "El usuario no posee perfil de pasajero", 403

            viajes_bd = []

            for item in viajes:
                cantidad = int(item.get("cantidad", 0))
                tipo = item.get("tipo_tramo")

                if cantidad <= 0 or tipo not in ("IDA", "RETORNO"):
                    connection.rollback()
                    return None, "Datos de tramo inválidos", 400

                viaje = repository.obtener_viaje_para_actualizar(
                    item["viaje_id"]
                )

                if viaje is None:
                    connection.rollback()
                    return None, "Uno de los viajes no existe", 404

                if viaje["estado"] != "DISPONIBLE":
                    connection.rollback()
                    return None, "Uno de los viajes no está disponible", 409

                if viaje["cupos"] < cantidad:
                    connection.rollback()
                    return None, "No existen cupos suficientes", 409

                if str(viaje["conductor_usuario_id"]) == str(usuario_id):
                    connection.rollback()
                    return None, "No puede reservar su propio viaje", 409

                viajes_bd.append((item, viaje))

            if len(viajes_bd) == 2:
                tipos = {item["tipo_tramo"] for item, _ in viajes_bd}
                if tipos != {"IDA", "RETORNO"}:
                    connection.rollback()
                    return None, "Debe seleccionar IDA y RETORNO", 400

                ida = next(
                    (item, v) for item, v in viajes_bd
                    if item["tipo_tramo"] == "IDA"
                )
                retorno = next(
                    (item, v) for item, v in viajes_bd
                    if item["tipo_tramo"] == "RETORNO"
                )

                fecha_ida = datetime.combine(
                    ida[1]["fecha"],
                    ida[1]["hora"]
                )
                fecha_retorno = datetime.combine(
                    retorno[1]["fecha"],
                    retorno[1]["hora"]
                )

                if fecha_retorno <= fecha_ida:
                    connection.rollback()
                    return None, "El retorno debe ser posterior a la ida", 409

            reserva_id = repository.crear_reserva(pasajero_id)
            orden = 1
            
            for item, viaje in viajes_bd:
                repository.crear_detalle(
                    reserva_id,
                    item["viaje_id"],
                    int(item["cantidad"]),
                    item["tipo_tramo"],
                    orden
                )
                repository.descontar_cupos(
                    item["viaje_id"],
                    int(item["cantidad"])
                )
                orden += 1

            connection.commit()
            return {
                "reserva_id": reserva_id
            }, "Reserva registrada correctamente", 201

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
            
    def cancelar(self, usuario_id, reserva_id):
        connection = get_connection()
        try:
            connection.begin()
            repository = ReservaRepository(connection)
            
            pasajero_id = repository.obtener_pasajero_id_por_usuario(usuario_id)
            if pasajero_id is None:
                connection.rollback()
                return None, "El usuario no posee perfil de pasajero", 403
                
            reserva = repository.obtener_reserva(reserva_id)
            if reserva is None:
                connection.rollback()
                return None, "Reserva no encontrada", 404
                
            if str(reserva["pasajero_id"]) != str(pasajero_id):
                connection.rollback()
                return None, "No puede cancelar una reserva que no es suya", 403
                
            if reserva["estado"] == "CANCELADA":
                connection.rollback()
                return None, "La reserva ya se encuentra cancelada", 409
                
            detalles = repository.obtener_detalles_activos_por_reserva(reserva_id)
            
            repository.cancelar_reserva(reserva_id)
            repository.cancelar_detalles_reserva(reserva_id)
            
            for detalle in detalles:
                v_id = detalle["viaje_id"]
                cant = detalle["cantidad"]
                # Need to lock the trip before returning seats, similar to creating a reservation
                repository.obtener_viaje_para_actualizar(v_id)
                repository.devolver_cupos(v_id, cant)
                
            connection.commit()
            return {"reserva_id": reserva_id}, "Reserva cancelada correctamente", 200
            
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
