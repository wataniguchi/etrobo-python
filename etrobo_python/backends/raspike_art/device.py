import time
from typing import Any, List, Tuple, Optional
import warnings

import etrobo_python

import libraspike_art_python as lib
from libraspike_art_python import pbio_port, pbio_color, hub_button, sound, pup_direction, pbio_error

def create_device(device_type: str, port: str, config: Optional[Tuple] = None) -> Any:
    if device_type == 'hub':
        return Hub()
    elif device_type == 'motor':
        return Motor(get_raspike_port(port))
    elif device_type == 'reversed_motor':
        return ReversedMotor(get_raspike_port(port))
    elif device_type == 'color_sensor':
        return ColorSensor(get_raspike_port(port))
    elif device_type == 'touch_sensor':
        return TouchSensor(get_raspike_port(port))
    elif device_type == 'sonar_sensor':
        return SonarSensor(get_raspike_port(port))
    elif device_type == 'gyro_sensor':
        return GyroSensor(config=config)
    else:
        raise NotImplementedError(f'Unsupported device: {device_type}')


def get_raspike_port(port: str) -> pbio_port:
    port_names = ('A', 'B', 'C', 'D', 'E', 'F')
    port_values = (
        pbio_port.ID_A,
        pbio_port.ID_B,
        pbio_port.ID_C,
        pbio_port.ID_D,
        pbio_port.ID_E,
        pbio_port.ID_F)

    if port in port_names:
        return port_values[port_names.index(port)]
    else:
        raise Exception(f'Unknown port: {port}')


class Hub(etrobo_python.Hub):
    def __init__(self) -> None:
        self.base_time = time.time()
        self.log = bytearray(5)

    def set_led(self, color: str) -> None:
        color_value = color.lower()[0]
        if color_value == 'r':
            lib.hub_light_on_color(pbio_color.RED)
        elif color_value == 'g':
            lib.hub_light_on_color(pbio_color.GREEN)
        elif color_value == 'o':
            lib.hub_light_on_color(pbio_color.ORANGE)
        else:
            lib.hub_light_on_color(pbio_color.BLACK)

    def get_time(self) -> float:
        return time.time() - self.base_time

    def get_battery_voltage(self) -> int:
        return lib.hub_battery_get_voltage()

    def get_battery_current(self) -> int:
        return lib.hub_battery_get_current()

    def play_speaker_tone(self, frequency: int, duration: float) -> None:
        if duration > 0:
            lib.hub_speaker_play_tone(frequency, int(1000 * duration))
        else:
            lib.hub_speaker_play_tone(frequency, sound.MANUAL_STOP)

    def set_speaker_volume(self, volume: int) -> None:
        lib.hub_speaker_set_volume(volume)

    def is_left_button_pressed(self) -> bool:
        return lib.hub_button_is_pressed(hub_button.LEFT)

    def is_right_button_pressed(self) -> bool:
        return lib.hub_button_is_pressed(hub_button.RIGHT)

    def is_up_button_pressed(self) -> bool:
        return lib.hub_button_is_pressed(hub_button.BT)

    def is_down_button_pressed(self) -> bool:
        return lib.hub_button_is_pressed(hub_button.CENTER)

    def get_acceleration(self) -> Tuple[float, float, float]:
        return lib.hub_imu_get_acceleration()

    def get_angular_velocity(self) -> Tuple[float, float, float]:
        return lib.hub_imu_get_angular_velocity()

    def get_log(self) -> bytes:
        self.log[:4] = int.to_bytes(int(self.get_time() * 1000), 4, 'big')
        self.log[4] = (
            int(self.is_left_button_pressed())
            | int(self.is_right_button_pressed()) << 1
            | int(self.is_up_button_pressed()) << 2
            | int(self.is_down_button_pressed()) << 3
        )

        return self.log


_MOTOR_DEVICES: List[Any] = []


def stop_all_motors() -> None:
    global _MOTOR_DEVICES

    for device in _MOTOR_DEVICES:
        lib.pup_motor_stop(device)


class _Motor(etrobo_python.Motor):
    def __init__(self, port: pbio_port, reversed: bool) -> None:
        self.port = port
        self.reversed = reversed
        self.device: Any = None
        self.brake = False
        self.log = bytearray(4)

        # Only motor on Spike Hub port B turns reverse direction,
        # following the build instruction for 2025
        if self.port == pbio_port.ID_B:
            self.reversed = not reversed

    def setup_device(self) -> None:
        global _MOTOR_DEVICES

        if self.device is None:
            self.device = lib.pup_motor_get_device(self.port)

            if self.reversed:
                lib.pup_motor_setup(self.device, pup_direction.COUNTERCLOCKWISE, True)
            else:
                lib.pup_motor_setup(self.device, pup_direction.CLOCKWISE, True)

            _MOTOR_DEVICES.append(self.device)

    def get_count(self) -> int:
        self.setup_device()
        return lib.pup_motor_get_count(self.device)

    def reset_count(self) -> None:
        self.setup_device()
        lib.pup_motor_reset_count(self.device)

    def set_power(self, power: int) -> None:
        self.setup_device()
        lib.pup_motor_set_power(self.device, power)

    def set_brake(self, brake: bool) -> None:
        self.setup_device()
        if brake:
            lib.pup_motor_brake(self.device)

    def get_log(self) -> bytes:
        self.log[:] = int.to_bytes(self.get_count() & 0xffffffff, 4, 'big')
        return self.log


class Motor(_Motor):
    def __init__(self, port: int) -> None:
        super().__init__(port, False)


class ReversedMotor(_Motor):
    def __init__(self, port: int) -> None:
        super().__init__(port, True)


class ColorSensor(etrobo_python.ColorSensor):
    def __init__(self, port: pbio_port) -> None:
        self.port = port
        self.device: Any = None
        self.mode = -1
        self.log = bytearray(5)

    def setup_device(self) -> None:
        if self.device is None:
            self.device = lib.pup_color_sensor_get_device(self.port)

    def get_brightness(self) -> int:
        self.setup_device()
        self.mode = 0
        return lib.pup_color_sensor_reflection(self.device)

    def get_ambient(self) -> int:
        self.setup_device()
        self.mode = 1
        return lib.pup_color_sensor_ambient(self.device)

    def get_raw_color(self) -> Tuple[int, int, int]:
        self.setup_device()
        self.mode = 2
        return lib.pup_color_sensor_rgb(self.device)

    def get_log(self) -> bytes:
        if self.mode == 0:
            self.log[0] = self.get_brightness()
            self.log[1] = 0
            self.log[2], self.log[3], self.log[4] = 0, 0, 0
        elif self.mode == 1:
            self.log[0] = 0
            self.log[1] = self.get_ambient()
            self.log[2], self.log[3], self.log[4] = 0, 0, 0
        elif self.mode == 2:
            self.log[0] = 0
            self.log[1] = 0
            self.log[2], self.log[3], self.log[4] = self.get_raw_color()

        return self.log


class TouchSensor(etrobo_python.TouchSensor):
    def __init__(self, port: pbio_port) -> None:
        self.port = port
        self.device: Any = None
        self.log = bytearray(1)

    def setup_device(self) -> None:
        if self.device is None:
            self.device = lib.pup_force_sensor_get_device(self.port)

    def is_pressed(self) -> bool:
        self.setup_device()
        return lib.pup_force_sensor_touched(self.device)

    def get_log(self) -> bytes:
        self.log[0] = int(self.is_pressed())
        return self.log


class SonarSensor(etrobo_python.SonarSensor):
    def __init__(self, port: pbio_port) -> None:
        self.port = port
        self.device: Any = None
        self.log = bytearray(2)

    def setup_device(self) -> None:
        if self.device is None:
            self.device = lib.pup_ultrasonic_sensor_get_device(self.port)

    def listen(self) -> bool:
        self.setup_device()
        return lib.pup_ultrasonic_sensor_presence(self.device)

    def get_distance(self) -> int:
        self.setup_device()
        return lib.pup_ultrasonic_sensor_distance(self.device)

    def get_log(self) -> bytes:
        self.log[:] = int.to_bytes(self.get_distance(), 2, 'big')
        return self.log


class GyroSensor(etrobo_python.GyroSensor):
    def __init__(self, config) -> None:
        self.log = bytearray(4)
        self.config = config
        self.initialized = False
        self.offset = 0.0
    
    def __initialize(self) -> None:
        if self.config is None:
            err = lib.hub_imu_initialize_by_default()
        else:
            err = lib.hub_imu_initialize(self.config)
        if err == pbio_error.SUCCESS:
            self.initialized = True

    def reset(self) -> None:
        if not self.initialized:
            self.__initialize()
        self.offset = lib.hub_imu_get_heading()

    def get_angle(self) -> int:
        if not self.initialized:
            self.__initialize()
        return round(lib.hub_imu_get_heading() - self.offset)

    def get_angular_velocity(self) -> int:
        if not self.initialized:
            self.__initialize()
        return round(lib.hub_imu_get_angular_velocity()[1])

    def get_angler_velocity(self) -> int:
        warnings.warn(
            'get_angler_velocity is deprecated, use get_angular_velocity instead.',
            DeprecationWarning)
        if not self.initialized:
            self.__initialize()
        return self.get_angular_velocity()

    def get_log(self) -> bytes:
        if not self.initialized:
            self.__initialize()
        self.log[:2] = int.to_bytes(self.get_angle(), 2, 'big', signed=True)
        self.log[2:] = int.to_bytes(self.get_anguler_velocity(), 2, 'big', signed=True)
        return self.log
