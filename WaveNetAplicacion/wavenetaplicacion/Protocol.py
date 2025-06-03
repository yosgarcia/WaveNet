import json
from typing import Any, Dict


class Protocol:
	"""
	Protocolo de capa de aplicación para WaveNet (Capa 4).
	Independiente de la capa 3. Serializa y deserializa mensajes en JSON.

	Estructura de mensaje estándar (dict):
	{
		"type": "REQUEST" | "RESPONSE" | "DATA",
		"resource": "<nombre_de_recurso>",
		"body": Any  # Datos o contenido del mensaje, puede ser str, dict, list, etc.
	}

	Si en el futuro se agregan campos o tipos, basta con actualizar
	el esquema de mensajes y mantener los métodos encode/decode.
	"""

	@staticmethod
	def encode(message: Dict[str, Any]) -> str:
		"""
		Serializa un mensaje (dict) en una cadena JSON.

		Args:
			message: Diccionario que debe incluir al menos las claves:
					 'type', 'resource' y 'body'.

		Returns:
			Una cadena JSON.

		Raises:
			ValueError: si falla la serialización.
		"""
		try:
			return json.dumps(message)
		except (TypeError, ValueError) as e:
			raise ValueError(f"Error al codificar el mensaje a JSON: {e}")

	@staticmethod
	def decode(message_str: str) -> Dict[str, Any]:
		"""
		Deserializa una cadena JSON en un mensaje (dict).

		Args:
			message_str: Cadena JSON recibida.

		Returns:
			Diccionario con los campos del mensaje.

		Raises:
			ValueError: si falla la deserialización o el formato es inválido.
		"""
		try:
			message = json.loads(message_str)
		except json.JSONDecodeError as e:
			raise ValueError(f"Error al decodificar la cadena JSON: {e}")

		if not isinstance(message, dict):
			raise ValueError("Mensaje JSON decodificado no es un diccionario.")

		# Validación básica de esquema
		required_keys = {"type", "resource", "body"}
		missing = required_keys - message.keys()
		if missing:
			raise ValueError(f"Faltan claves obligatorias en el mensaje: {missing}")

		return message  # type: ignore[return-value]
