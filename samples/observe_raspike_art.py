import argparse
from typing import Any

from etrobo_python import (ColorSensor, ETRobo, GyroSensor, Hub, Motor,
                           SonarSensor, TouchSensor)


def print_obtained_values_in_realworld(
    hub: Hub,
    right_motor: Motor,
    left_motor: Motor,
    touch_sensor: TouchSensor,
    color_sensor: ColorSensor,
    sonar_sensor: SonarSensor,
    gyro_sensor: GyroSensor,
) -> None:
    x_accel, y_accel, z_accel = hub.get_acceleration()  # type: ignore
    x_angv, y_angv, z_angv = hub.get_angular_velocity()  # type: ignore
    lines = [
        'Hub: time={}'.format(hub.get_time()),
        'Hub: battery_voltage={}'.format(hub.get_battery_voltage()),
        'Hub: battery_current={}'.format(hub.get_battery_current()),
        'Hub: acceleration=({}, {}, {})'.format(x_accel, y_accel, z_accel),
        'Hub: angular_velocity=({}, {}, {})'.format(x_angv, y_angv, z_angv),
        'RightMotor: count={}'.format(right_motor.get_count()),
        'LeftMotor: count={}'.format(left_motor.get_count()),
        'TouchSensor: pressed={}'.format(touch_sensor.is_pressed()),
        'ColorSensor: raw_color={}'.format(color_sensor.get_raw_color()),
        'SonarSensor: distance={}'.format(sonar_sensor.get_distance()),
        'GyroSensor: angular_velocity={}'.format(gyro_sensor.get_angler_velocity()),
        'GyroSensor: angle={}'.format(gyro_sensor.get_angle())
    ]

    right_motor.set_brake(True)

    print('\n'.join(lines))


def run(backend: str, **kwargs: Any) -> None:
    (ETRobo(backend=backend)
     .add_hub(name='hub')
     .add_device(name='right_motor', device_type=Motor, port='A')
     .add_device(name='left_motor', device_type=Motor, port='B')
     .add_device(name='touch_sensor', device_type=TouchSensor, port='D')
     .add_device(name='color_sensor', device_type=ColorSensor, port='E')
     .add_device(name='sonar_sensor', device_type=SonarSensor, port='F')
     .add_device(name='gyro_sensor', device_type=GyroSensor, port='',
        config=[2.0, 2500.0,
        [-1.61239, -1.485107, -0.2945677], [360.4545, 356.9208, 363.781],
        [10016.18, -9657.935, 9823.967, -9957.187, 9766.231, -9970.058]])
     .add_handler(print_obtained_values_in_realworld)
     .dispatch(**kwargs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='/dev/USB_SPIKE', help='Serial port.')
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='raspike_art', port=args.port, interval=0.04, logfile=args.logfile)
