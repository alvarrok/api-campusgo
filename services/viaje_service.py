from database import get_connection
from repositories.viaje_repository import ViajeRepository
from datetime import timedelta, date


class ViajeService:

    def crear(self, usuario_id, datos):
        obligatorios = ["origen", "destino", "fecha", "hora", "cupos", "precio"]

        if any(campo not in datos for campo in obligatorios):
            return None, "Faltan datos obligatorios", 400

        if int(datos.get("cupos", 0)) <= 0:
            return None, "Los cupos deben ser mayores que cero", 400

        if float(datos.get("precio", -1)) < 0:
            return None, "El precio no puede ser negativo", 400

        connection = get_connection()

        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)

            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            if repository.existe_viaje_duplicado(conductor_id, datos["fecha"], datos["hora"], datos["origen"], datos["destino"]):
                return None, "El viaje ya existe (duplicado)", 409

            viaje_id = repository.crear(conductor_id, datos)
            connection.commit()

            return {"viaje_id": viaje_id}, "Viaje creado correctamente", 201

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def listar(self, filtros):
        precio_min = filtros.get("precio_min")
        precio_max = filtros.get("precio_max")
        
        if precio_min is not None:
            try:
                precio_min = float(precio_min)
            except ValueError:
                return None, "precio_min debe ser numerico", 400
                
        if precio_max is not None:
            try:
                precio_max = float(precio_max)
            except ValueError:
                return None, "precio_max debe ser numerico", 400
                
        if precio_min is not None and precio_max is not None and precio_min > precio_max:
            return None, "precio_min debe ser menor o igual a precio_max", 400
            
        desde = filtros.get("desde")
        if desde is not None:
            try:
                date.fromisoformat(desde)
            except ValueError:
                return None, "El formato de fecha 'desde' es invalido", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viajes = repository.listar(
                origen=filtros.get("origen"),
                destino=filtros.get("destino"),
                fecha=filtros.get("fecha"),
                estado=filtros.get("estado"),
                precio_min=precio_min,
                precio_max=precio_max,
                solo_disponibles=filtros.get("solo_disponibles"),
                desde=desde
            )
            for viaje in viajes:
                if isinstance(viaje.get("hora"), timedelta):
                    viaje["hora"]=str(viaje["hora"])
                if isinstance(viaje.get("fecha"), date):
                    viaje["fecha"]=viaje["fecha"].isoformat()

            return viajes, "Viajes obtenidos correctamente", 200
        finally:
            connection.close()

    def listar_mis_viajes(self, usuario_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)

            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403
                
            viajes = repository.listar(conductor_id=conductor_id)
            for viaje in viajes:
                if isinstance(viaje.get("hora"), timedelta):
                    viaje["hora"]=str(viaje["hora"])
                if isinstance(viaje.get("fecha"), date):
                    viaje["fecha"]=viaje["fecha"].isoformat()

            return viajes, "Mis viajes obtenidos correctamente", 200
        finally:
            connection.close()

    def obtener(self, viaje_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if isinstance(viaje.get("hora"), timedelta):
                viaje["hora"]=str(viaje["hora"])

            if isinstance(viaje.get("fecha"), date):
                viaje["fecha"]=viaje["fecha"].isoformat()

            return viaje, "Viaje obtenido correctamente", 200
        finally:
            connection.close()

    def actualizar(self, usuario_id, viaje_id, datos):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403

            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, "El estado actual no permite modificar el viaje", 409

            repository.actualizar(viaje_id, datos)
            connection.commit()

            return {"viaje_id": viaje_id}, "Viaje actualizado correctamente", 200

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
            
    def actualizar_cupos(self, usuario_id, viaje_id, datos):
        if "cupos" not in datos:
            return None, "Se requiere el campo cupos", 400
            
        try:
            cupos = int(datos["cupos"])
            if cupos < 0:
                return None, "Los cupos no pueden ser menores que cero", 400
        except ValueError:
            return None, "Cupos debe ser numerico", 400
            
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403

            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, "El estado actual no permite modificar el viaje", 409

            repository.actualizar_cupos(viaje_id, cupos)
            connection.commit()

            return {"viaje_id": viaje_id}, "Cupos actualizados correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
            
    def cambiar_estado(self, usuario_id, viaje_id, datos):
        nuevo_estado = datos.get("estado")
        estados_permitidos = ["DISPONIBLE", "COMPLETO", "FINALIZADO", "CANCELADO"]
        
        if nuevo_estado not in estados_permitidos:
            return None, "Estado no valido", 400
            
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403

            if viaje["estado"] == "CANCELADO" and nuevo_estado == "DISPONIBLE":
                return None, "No se puede pasar de CANCELADO a DISPONIBLE", 409
                
            repository.cambiar_estado(viaje_id, nuevo_estado)
            connection.commit()

            return {"viaje_id": viaje_id}, "Estado actualizado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def cancelar(self, usuario_id, viaje_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede cancelar un viaje de otro conductor", 403

            if viaje["estado"] == "FINALIZADO":
                return None, "No se puede cancelar un viaje finalizado", 409
                
            if viaje["estado"] == "CANCELADO":
                return None, "El viaje ya se encuentra cancelado", 409

            repository.cancelar(viaje_id)
            connection.commit()

            return {"viaje_id": viaje_id}, "Viaje cancelado correctamente", 200

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def resumen_viajes(self, usuario_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403
                
            resumen = repository.resumen_por_estado(conductor_id)
            return resumen, "Resumen obtenido correctamente", 200
        finally:
            connection.close()
