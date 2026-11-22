"""
Proyecto: Sistema Integral de Gestión de Clientes, Servicios y Reservas - Software FJ
Autor: Miguelangel Corwin Espitia
Programa: Ingeniería de Sistemas
Modalidad: Entrega individual (con aval) - Fase 4, Anexo 3 (Ejercicio 1)
Sin uso de base de datos (gestión en memoria con listas y registro en archivo de logs).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from functools import singledispatchmethod
import logging
from typing import Optional


# ==========================================
# 1. CONFIGURACIÓN DE LOGS (SIN BASE DE DATOS)
# ==========================================
logger = logging.getLogger("SoftwareFJ")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler("software_fj.log", mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# ==========================================
# 2. EXCEPCIONES PERSONALIZADAS
# ==========================================
class ErrorSoftwareFJ(Exception):
    """Excepción base del sistema Software FJ."""


class ErrorValidacionDatos(ErrorSoftwareFJ):
    """Error por datos inválidos, vacíos o parámetros faltantes."""


class ErrorOperacionNoPermitida(ErrorSoftwareFJ):
    """Error por transiciones de estado o acciones no válidas."""


class ErrorDisponibilidadServicio(ErrorSoftwareFJ):
    """Error cuando un servicio no está disponible o no cumple requisitos."""


class ErrorCalculoFinanciero(ErrorSoftwareFJ):
    """Error en cálculos de costos, descuentos, impuestos o duraciones."""


# ==========================================
# 3. CLASE ABSTRACTA GENERAL
# ==========================================
class EntidadBase(ABC):
    """Representa una entidad general dentro del sistema."""

    def __init__(self, id_entidad: str, nombre: str) -> None:
        if not isinstance(id_entidad, str) or not id_entidad.strip():
            raise ErrorValidacionDatos("El ID de la entidad es obligatorio y debe ser texto.")
        if not isinstance(nombre, str) or len(nombre.strip()) < 2:
            raise ErrorValidacionDatos("El nombre debe tener al menos 2 caracteres.")

        self._id_entidad = id_entidad.strip().upper()
        self._nombre = nombre.strip()
        self._fecha_creacion = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, nuevo_nombre: str) -> None:
        if not isinstance(nuevo_nombre, str) or len(nuevo_nombre.strip()) < 2:
            raise ErrorValidacionDatos("El nuevo nombre debe tener al menos 2 caracteres.")
        self._nombre = nuevo_nombre.strip()

    @abstractmethod
    def describir(self) -> str:
        """Retorna una descripción legible de la entidad."""


# ==========================================
# 4. CLASE CLIENTE (ENCAPSULACIÓN Y VALIDACIÓN)
# ==========================================
class Cliente(EntidadBase):
    """Gestiona los datos personales encapsulados y validados de un cliente."""

    def __init__(self, id_cliente: str, nombre: str, email: str, telefono: str) -> None:
        super().__init__(id_cliente, nombre)
        self.email = email
        self.telefono = telefono
        self._activo = True

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        if not isinstance(valor, str) or "@" not in valor or "." not in valor.split("@")[-1]:
            raise ErrorValidacionDatos(f"Correo electrónico inválido: '{valor}'.")
        self._email = valor.strip().lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        limpio = "".join(ch for ch in str(valor) if ch.isdigit())
        if len(limpio) < 7:
            raise ErrorValidacionDatos(f"Teléfono inválido ('{valor}'): debe tener al menos 7 dígitos.")
        self._telefono = limpio

    @property
    def activo(self) -> bool:
        return self._activo

    def desactivar(self) -> None:
        self._activo = False

    def activar(self) -> None:
        self._activo = True

    def describir(self) -> str:
        estado = "Activo" if self._activo else "Inactivo"
        return f"Cliente [{self._id_entidad}] {self._nombre} | Email: {self._email} | Tel: {self._telefono} | {estado}"


# ==========================================
# 5. CLASE ABSTRACTA SERVICIO Y DERIVADAS
# ==========================================
class Servicio(EntidadBase):
    """Clase base abstracta para todos los servicios de Software FJ."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, disponible: bool = True) -> None:
        super().__init__(id_servicio, nombre)
        if not isinstance(tarifa_base, (int, float)) or tarifa_base <= 0:
            raise ErrorValidacionDatos("La tarifa base debe ser un número mayor que cero.")
        self._tarifa_base = float(tarifa_base)
        self._disponible = bool(disponible)

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self._disponible = bool(estado)

    @abstractmethod
    def validar_parametros(self, duracion: float, **kwargs) -> None:
        """Valida duración y parámetros específicos del servicio."""

    @abstractmethod
    def _calcular_subtotal(self, duracion: float, **kwargs) -> float:
        """Calcula el subtotal antes de descuentos o impuestos."""

    @singledispatchmethod
    def calcular_costo(self, duracion_o_param, descuento_pct: float = 0.0, impuesto_pct: float = 0.19) -> float:
        """
        Método sobrecargado:
        - Si recibe duración numérica: calcula costo con descuento (%) e impuesto (%).
        - Si recibe un diccionario con {'duracion': ..., 'descuento_pct': ..., 'impuesto_pct': ...}: calcula igual.
        """
        if not isinstance(duracion_o_param, (int, float)):
            raise ErrorValidacionDatos("Duración inválida para calcular costo.")
        return self._calcular_desde_valores(float(duracion_o_param), descuento_pct, impuesto_pct)

    @calcular_costo.register
    def _(self, parametros: dict) -> float:
        if not isinstance(parametros, dict) or "duracion" not in parametros:
            raise ErrorValidacionDatos("El diccionario de cálculo debe incluir la clave 'duracion'.")
        return self._calcular_desde_valores(
            float(parametros["duracion"]),
            float(parametros.get("descuento_pct", 0.0)),
            float(parametros.get("impuesto_pct", 0.19)),
        )

    def _calcular_desde_valores(self, duracion: float, descuento_pct: float, impuesto_pct: float) -> float:
        try:
            self.validar_parametros(duracion)
            if not (0 <= descuento_pct < 100):
                raise ErrorCalculoFinanciero("El porcentaje de descuento debe estar entre 0 y 99.9.")
            if impuesto_pct < 0:
                raise ErrorCalculoFinanciero("El porcentaje de impuesto no puede ser negativo.")

            subtotal = self._calcular_subtotal(duracion)
            if subtotal <= 0:
                raise ErrorCalculoFinanciero("El subtotal calculado no es válido.")

            con_descuento = subtotal * (1 - descuento_pct / 100.0)
            total = con_descuento * (1 + impuesto_pct)
            return round(total, 2)
        except ErrorSoftwareFJ:
            raise
        except Exception as exc:
            raise ErrorCalculoFinanciero("Error inesperado al calcular el costo del servicio.") from exc


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas (duración en horas)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_hora: float, capacidad: int, disponible: bool = True) -> None:
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if capacidad <= 0:
            raise ErrorValidacionDatos("La capacidad de la sala debe ser mayor que cero.")
        self.capacidad = capacidad

    def validar_parametros(self, duracion: float, **kwargs) -> None:
        if not isinstance(duracion, (int, float)) or duracion <= 0:
            raise ErrorValidacionDatos("La reserva de sala requiere una duración mayor a 0 horas.")
        if duracion > 12:
            raise ErrorDisponibilidadServicio("Una sala no puede reservarse por más de 12 horas continuas.")

    def _calcular_subtotal(self, duracion: float, **kwargs) -> float:
        return self._tarifa_base * duracion

    def describir(self) -> str:
        return f"Sala [{self._id_entidad}] {self._nombre} (Cap. {self.capacidad} pers.) - ${self._tarifa_base:,.2f}/h"


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de equipos (duración en días)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_dia: float, codigo_serie: str, disponible: bool = True) -> None:
        super().__init__(id_servicio, nombre, tarifa_dia, disponible)
        if not codigo_serie or not codigo_serie.strip():
            raise ErrorValidacionDatos("El código de serie del equipo es obligatorio.")
        self.codigo_serie = codigo_serie.strip().upper()

    def validar_parametros(self, duracion: float, **kwargs) -> None:
        if not isinstance(duracion, (int, float)) or duracion < 1:
            raise ErrorValidacionDatos("El alquiler de equipo requiere al menos 1 día.")

    def _calcular_subtotal(self, duracion: float, **kwargs) -> float:
        return (self._tarifa_base * duracion) + 15000.0

    def describir(self) -> str:
        return f"Equipo [{self._id_entidad}] {self._nombre} (Serie: {self.codigo_serie}) - ${self._tarifa_base:,.2f}/día"


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para asesorías técnicas (duración en horas)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_hora: float, especialidad: str, disponible: bool = True) -> None:
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if not especialidad or not especialidad.strip():
            raise ErrorValidacionDatos("La especialidad de la asesoría es obligatoria.")
        self.especialidad = especialidad.strip()

    def validar_parametros(self, duracion: float, **kwargs) -> None:
        if not isinstance(duracion, (int, float)) or duracion < 0.5:
            raise ErrorValidacionDatos("La asesoría requiere como mínimo 0.5 horas (30 minutos).")

    def _calcular_subtotal(self, duracion: float, **kwargs) -> float:
        return self._tarifa_base * duracion

    def describir(self) -> str:
        return f"Asesoría [{self._id_entidad}] {self._nombre} ({self.especialidad}) - ${self._tarifa_base:,.2f}/h"


# ==========================================
# 6. CLASE RESERVA Y GESTOR DEL SISTEMA
# ==========================================
class Reserva:
    """Integra cliente, servicio, duración y estado con manejo de excepciones."""

    ESTADOS_VALIDOS = {"PENDIENTE", "CONFIRMADA", "CANCELADA"}

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: float,
        descuento_pct: float = 0.0,
    ) -> None:
        if not id_reserva or not id_reserva.strip():
            raise ErrorValidacionDatos("El ID de reserva es obligatorio.")
        if not isinstance(cliente, Cliente):
            raise ErrorValidacionDatos("Debe asociarse un objeto Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ErrorValidacionDatos("Debe asociarse un objeto Servicio válido.")

        self.id_reserva = id_reserva.strip().upper()
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.descuento_pct = descuento_pct
        self.estado = "PENDIENTE"
        self.total_estimado: Optional[float] = None

    def procesar(self) -> float:
        """Valida disponibilidad, estado del cliente y calcula el total de la reserva."""
        try:
            if not self.cliente.activo:
                raise ErrorOperacionNoPermitida(f"El cliente {self.cliente.id_entidad} está inactivo.")
            if not self.servicio.disponible:
                raise ErrorDisponibilidadServicio(f"El servicio {self.servicio.id_entidad} no está disponible.")
            if self.estado == "CANCELADA":
                raise ErrorOperacionNoPermitida("No se puede procesar una reserva cancelada.")

            total = self.servicio.calcular_costo(self.duracion, descuento_pct=self.descuento_pct)
        except ErrorSoftwareFJ as exc:
            raise ErrorOperacionNoPermitida(f"Fallo al procesar la reserva {self.id_reserva}.") from exc
        else:
            self.total_estimado = total
            return total
        finally:
            logger.info(
                "Intento de procesamiento en reserva %s | Estado actual: %s | Total estimado: %s",
                self.id_reserva,
                self.estado,
                self.total_estimado,
            )

    def confirmar(self) -> None:
        if self.estado == "CANCELADA":
            raise ErrorOperacionNoPermitida(f"La reserva {self.id_reserva} ya fue cancelada y no puede confirmarse.")
        if self.total_estimado is None:
            self.procesar()
        self.estado = "CONFIRMADA"
        logger.info("Reserva %s CONFIRMADA para el cliente %s.", self.id_reserva, self.cliente.id_entidad)

    def cancelar(self, motivo: str = "Sin motivo especificado") -> None:
        if self.estado == "CANCELADA":
            raise ErrorOperacionNoPermitida(f"La reserva {self.id_reserva} ya se encuentra cancelada.")
        self.estado = "CANCELADA"
        logger.warning("Reserva %s CANCELADA. Motivo: %s", self.id_reserva, motivo)


class SistemaGestionSoftwareFJ:
    """Gestor en memoria (sin base de datos) para clientes, servicios y reservas."""

    def __init__(self) -> None:
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []

    def registrar_cliente(self, cliente: Cliente) -> None:
        if any(c.id_entidad == cliente.id_entidad for c in self.clientes):
            raise ErrorValidacionDatos(f"Ya existe un cliente con ID {cliente.id_entidad}.")
        self.clientes.append(cliente)
        logger.info("Cliente registrado: %s", cliente.describir())

    def registrar_servicio(self, servicio: Servicio) -> None:
        if any(s.id_entidad == servicio.id_entidad for s in self.servicios):
            raise ErrorValidacionDatos(f"Ya existe un servicio con ID {servicio.id_entidad}.")
        self.servicios.append(servicio)
        logger.info("Servicio registrado: %s", servicio.describir())

    def crear_y_procesar_reserva(self, reserva: Reserva, confirmar_si_valida: bool = True) -> Optional[float]:
        try:
            total = reserva.procesar()
            if confirmar_si_valida:
                reserva.confirmar()
            self.reservas.append(reserva)
            return total
        except ErrorSoftwareFJ as exc:
            causa = f" (Causa: {exc.__cause__})" if exc.__cause__ else ""
            logger.error("Error en reserva %s: %s%s", reserva.id_reserva, exc, causa)
            print(f"[ERROR CONTROLADO] Reserva {reserva.id_reserva}: {exc}{causa}")
            return None


# ==========================================
# 7. SIMULACIÓN DE 12 OPERACIONES COMPLETAS
# ==========================================
def ejecutar_simulacion() -> None:
    sistema = SistemaGestionSoftwareFJ()
    print("=== INICIO DE SIMULACIÓN SOFTWARE FJ (SIN BASE DE DATOS) ===\n")

    operaciones = [
        ("Op 1 - Cliente válido", lambda: sistema.registrar_cliente(
            Cliente("CLI-01", "Laura Gómez", "laura.gomez@empresa.co", "3001234567")
        )),
        ("Op 2 - Segundo cliente válido", lambda: sistema.registrar_cliente(
            Cliente("CLI-02", "Carlos Ruiz", "carlos.ruiz@correo.com", "3159876543")
        )),
        ("Op 3 - Cliente inválido (email)", lambda: sistema.registrar_cliente(
            Cliente("CLI-03", "Andrés Pérez", "correo_sin_arroba", "3015551122")
        )),
        ("Op 4 - Cliente duplicado", lambda: sistema.registrar_cliente(
            Cliente("CLI-01", "Laura Duplicada", "otra@empresa.co", "3001234567")
        )),
        ("Op 5 - Crear ReservaSala", lambda: sistema.registrar_servicio(
            ReservaSala("SRV-SAL-1", "Sala Auditorio Norte", 80000, capacidad=25, disponible=True)
        )),
        ("Op 6 - Crear AlquilerEquipo", lambda: sistema.registrar_servicio(
            AlquilerEquipo("SRV-EQ-1", "Servidor Portátil Lab", 120000, codigo_serie="SN-99482", disponible=True)
        )),
        ("Op 7 - Crear Asesoria no disponible", lambda: sistema.registrar_servicio(
            AsesoriaEspecializada("SRV-ASE-1", "Arquitectura Cloud", 150000, especialidad="DevOps", disponible=False)
        )),
        ("Op 8 - Servicio inválido (tarifa <= 0)", lambda: sistema.registrar_servicio(
            ReservaSala("SRV-SAL-2", "Sala Pequeña", -10000, capacidad=6)
        )),
        ("Op 9 - Reserva exitosa de Sala", lambda: sistema.crear_y_procesar_reserva(
            Reserva("RES-001", sistema.clientes[0], sistema.servicios[0], duracion=3, descuento_pct=10)
        )),
        ("Op 10 - Reserva exitosa de Equipo", lambda: sistema.crear_y_procesar_reserva(
            Reserva("RES-002", sistema.clientes[1], sistema.servicios[1], duracion=2, descuento_pct=0)
        )),
        ("Op 11 - Reserva fallida (servicio no disponible)", lambda: sistema.crear_y_procesar_reserva(
            Reserva("RES-003", sistema.clientes[0], sistema.servicios[2], duracion=2)
        )),
        ("Op 12 - Reserva fallida (>12h en sala)", lambda: sistema.crear_y_procesar_reserva(
            Reserva("RES-004", sistema.clientes[1], sistema.servicios[0], duracion=15)
        )),
    ]

    for titulo, accion in operaciones:
        try:
            resultado = accion()
            print(f"[OK] {titulo} -> {resultado if resultado is not None else 'Completado'}")
            logger.info("Operación exitosa: %s", titulo)
        except ErrorSoftwareFJ as exc:
            print(f"[EXCEPCIÓN CONTROLADA] {titulo} -> {exc}")
            logger.error("Error controlado en %s: %s", titulo, exc)
        except Exception as exc:
            print(f"[ERROR INESPERADO] {titulo} -> {exc}")
            logger.critical("Error inesperado en %s: %s", titulo, exc)

    print(f"\nResumen en memoria -> Clientes: {len(sistema.clientes)} | Servicios: {len(sistema.servicios)} | Reservas: {len(sistema.reservas)}")
    print("Revisa 'software_fj.log' para el historial detallado de eventos y errores.")


if __name__ == "__main__":
    ejecutar_simulacion()
