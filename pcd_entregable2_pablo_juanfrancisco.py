import asyncio
import datetime as dt
import random
from functools import reduce
import math
from abc import ABC, abstractmethod


# Define la clase Singleton
class Singleton:
    _unicaInstancia = None

    def __init__(self):
        pass

    @classmethod
    def obtener_instancia(cls):
        if not cls._unicaInstancia:
            cls._unicaInstancia = cls()
        return cls._unicaInstancia

class IoTManager(Singleton):
    def __init__(self):
        self.sensor_temperatura = TemperatureSensor()
        self.estrategia = Media()
        self.calcular_handler = CalcularEstadisticosHandler(self.estrategia)
        self.umbral_handler = ComprobarUmbralHandler()
        self.aumento_handler = AumentoTemperaturaHandler()
        self.iot_system = IoTSystem(self.calcular_handler)

        # Configuramos la cadena de responsabilidad
        self.calcular_handler.successor = self.umbral_handler
        self.umbral_handler.successor = self.aumento_handler

        # Agregamos el sistema IoT como observador del sensor de temperatura
        self.sensor_temperatura.add_observer(self.iot_system)

    def ejecutar_simulacion(self):
        asyncio.run(self.sensor_temperatura.simulate_temperature_reading())


# Define las clases Observable y Observer
class Observable:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self, data):
        for observer in self.observers:
            observer.update(data)

class Observer:
    def update(self, data):
        pass

# Define la clase Sensor de Temperatura
class TemperatureSensor(Observable):
    async def simulate_temperature_reading(self):
        while True:
            timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Obtener la marca de tiempo actual
            t = 20 + (random.random() * 15)  # Simular la lectura de temperatura
            data = (timestamp, round(t,2))  # Crear una tupla (timestamp, temperatura)
            self.notify_observers(data)  # Notificar a los observadores con los datos
            await asyncio.sleep(5)  # Esperar 5 segundos para la siguiente lectura

# Define la clase Sistema IoT
class IoTSystem(Observer):
    def __init__(self,handler):
        super().__init__()
        self.handler = handler
        self.lista_datos = []

    def update(self, data):
        self.lista_datos.append(data)
        print("Nuevo dato de temperatura recibido:", data)
        self.handler.handle_request(data)
        return self.lista_datos


# R3:
# 1. STRATEGY

class ContextoCalculoEstadisticos:
    def __init__(self, estrategia=None):
        self.estrategia = estrategia

    def cambiar_estrategia(self, estrategia_nueva):
        self.estrategia = estrategia_nueva

    def calculo_estadisticos(self, datos):
        return self.estrategia.calculo(datos)


class Estrategia(ABC):
    @abstractmethod
    def calculo(self, datos):
        pass


class Media(Estrategia):
    def __init__(self):
        self.nombre = 'Media'

    def calculo(self, datos):
        return reduce(lambda x, y: x + y, datos) / len(datos)


class DesvTipica(Estrategia):
    def __init__(self):
        self.nombre = 'Desviación Típica'

    def calculo(self, datos):
        media = reduce(lambda x, y: x + y, datos) / len(datos)
        desviaciones = list(map(lambda x: (x - media) ** 2, datos))
        suma_cuadrados_desviaciones = reduce(lambda x, y: x + y, desviaciones)
        desviacion_tipica = math.sqrt(suma_cuadrados_desviaciones / len(datos))
        return desviacion_tipica

class Cuantiles(Estrategia):
    def __init__(self):
        self.nombre = 'Cuantiles'

    def calculo(self, datos):
        lista_ordenada = sorted(datos)
        return list(map(lambda p: lista_ordenada[int((len(lista_ordenada)-1) * p)], [0.25, 0.5, 0.75]))
    
class MaxMin(Estrategia):
    def __init__(self):
        self.nombre = 'Máximo y mínimo'

    def calculo(self, datos):
        max = reduce(lambda a, b: a if a > b else b, datos)
        min = reduce(lambda a, b: a if a < b else b, datos)
        return {'Máximo':max, 'Mínimo':min}
    
# 2 y 3 CHAIN OF RESPONSIBILITY

class TemperatureHandler:
    def __init__(self, successor=None):
        self.successor = successor

    def handle_request(self, data):
        pass


# Primer Paso: Calcular estadísticas de temperatura
class CalcularEstadisticosHandler(TemperatureHandler):
    def __init__(self, strategy, successor=None):
        super().__init__(successor)
        self.strategy = strategy
        self.temperaturas_recientes = []

    def handle_request(self, data):
        # Seleccionamos las temperaturas de los últimos 60 segundos
        fecha_hora_hace_un_min = dt.datetime.now() - dt.timedelta(minutes=1)
        if dt.datetime.strptime(data[0], '%Y-%m-%d %H:%M:%S') > fecha_hora_hace_un_min:
            self.temperaturas_recientes.append(data[1])
        if len(self.temperaturas_recientes)>12:
            del(self.temperaturas_recientes[0])        
        estadisticos = ContextoCalculoEstadisticos(self.strategy).calculo_estadisticos(self.temperaturas_recientes)
        print(f'El estadístico elegido ({self.strategy.nombre}) de los últimos 60 segundos vale: {estadisticos}')
        if self.successor:
            self.successor.handle_request(data)


# Segundo Paso: Comprobar el umbral de temperatura
class ComprobarUmbralHandler(TemperatureHandler):
    def __init__(self, successor=None):
        pass

    def handle_request(self, data):
        timestamp, temperature = data
        umbral = 30  # Se establece el umbral a 30ºC
        if temperature > umbral:
            print(f"Temperatura ({temperature}) por encima del umbral ({umbral})")
        if self.successor:
            self.successor.handle_request(data)

# Tercer Paso: Comprobar aumento de temperatura
class AumentoTemperaturaHandler(TemperatureHandler):
    def __init__(self, successor=None):
        super().__init__(successor)
        self.temperaturas_recientes = []

    def handle_request(self, data):
        # Seleccionamos las temperaturas de los últimos 30 segundos
        fecha_hora_hace_30_seg = dt.datetime.now() - dt.timedelta(seconds=30)
        if dt.datetime.strptime(data[0], '%Y-%m-%d %H:%M:%S') > fecha_hora_hace_30_seg:
            self.temperaturas_recientes.append(data[1])
        if len(self.temperaturas_recientes)>6:
            del(self.temperaturas_recientes[0])
        cambio_temperatura = sum(self.temperaturas_recientes[i] - self.temperaturas_recientes[i + 1] for i in
                                 range(len(self.temperaturas_recientes) - 1))
        if cambio_temperatura > 10:
            print("La temperatura ha aumentado más de 10º en los últimos 30 segundos")

if __name__ == '__main__':
    manager = IoTManager.obtener_instancia()
    manager.ejecutar_simulacion()

