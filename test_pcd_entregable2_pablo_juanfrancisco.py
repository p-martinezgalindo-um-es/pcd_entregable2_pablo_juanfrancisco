import pytest
import asyncio
from unittest.mock import MagicMock
from pcd_entregable2_pablo_juanfrancisco import IoTManager, TemperatureSensor, CalcularEstadisticosHandler, ComprobarUmbralHandler, AumentoTemperaturaHandler

@pytest.fixture
def mock_sensor():
    sensor = TemperatureSensor()
    sensor.notify_observers = MagicMock()
    return sensor

@pytest.fixture
def manager_with_mocked_sensor(mock_sensor):
    manager = IoTManager.obtener_instancia()
    manager.sensor_temperatura = mock_sensor
    return manager

@pytest.mark.asyncio
async def test_sensor_simulation(mock_sensor):
    await mock_sensor.simulate_temperature_reading()
    assert mock_sensor.notify_observers.called

def test_calculate_statistics_handler():
    handler = CalcularEstadisticosHandler(strategy=None)
    handler.temperaturas_recientes = [20, 21, 22, 23, 24, 25]
    handler.handle_request(('2024-05-11 12:00:00', 25))
    assert handler.temperaturas_recientes == [21, 22, 23, 24, 25]

def test_threshold_handler(capfd):
    handler = ComprobarUmbralHandler()
    handler.handle_request(('2024-05-11 12:00:00', 31))
    out, _ = capfd.readouterr()
    assert "Temperatura (31) por encima del umbral (30)" in out

def test_temperature_increase_handler(capfd):
    handler = AumentoTemperaturaHandler()
    handler.handle_request(('2024-05-11 12:00:00', 25))
    handler.handle_request(('2024-05-11 12:00:05', 27))
    handler.handle_request(('2024-05-11 12:00:10', 30))
    out, _ = capfd.readouterr()
    assert "La temperatura ha aumentado más de 10º en los últimos 30 segundos" in out

