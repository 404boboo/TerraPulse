from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RobotProfile:
    key: str
    display_name: str
    robot_type: str
    description: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    diagnostic_categories: tuple[str, ...]
    supported_metrics: tuple[str, ...]
    component_groups: dict[str, tuple[str, ...]]


QUADRUPED_JOINTS: tuple[str, ...] = (
    "fl_hip",
    "fl_thigh",
    "fl_calf",
    "fr_hip",
    "fr_thigh",
    "fr_calf",
    "rl_hip",
    "rl_thigh",
    "rl_calf",
    "rr_hip",
    "rr_thigh",
    "rr_calf",
)


_PROFILES: dict[str, RobotProfile] = {
    "quadruped": RobotProfile(
        key="quadruped",
        display_name="Quadruped Robot",
        robot_type="quadruped",
        description="Legged inspection robot profile matching the current TerraPulse CSV telemetry pipeline.",
        required_fields=(
            "mission_time_s",
            "battery_percent",
            "total_current_a",
            "status",
        ),
        optional_fields=(
            "timestamp",
            "x_m",
            "y_m",
            "z_m",
            "pack_voltage_v",
            "terrain_slope_deg",
            "signal_strength_percent",
            "imu_roll_deg",
            "imu_pitch_deg",
            "imu_yaw_deg",
            "robot_mode",
            "event",
            "waypoint",
            "joint telemetry for 12 joints",
        ),
        diagnostic_categories=(
            "thermal",
            "current",
            "torque",
            "terrain",
            "stability",
            "communication",
            "battery",
            "stalled_motion",
            "mission_risk",
        ),
        supported_metrics=(
            "battery_percent",
            "pack_voltage_v",
            "total_current_a",
            "terrain_slope_deg",
            "signal_strength_percent",
            "imu_roll_deg",
            "imu_pitch_deg",
            "imu_yaw_deg",
            "joint_temperature",
            "joint_current",
            "joint_torque",
            "route_risk_score",
            "event_count",
        ),
        component_groups={
            "front_left_leg": ("fl_hip", "fl_thigh", "fl_calf"),
            "front_right_leg": ("fr_hip", "fr_thigh", "fr_calf"),
            "rear_left_leg": ("rl_hip", "rl_thigh", "rl_calf"),
            "rear_right_leg": ("rr_hip", "rr_thigh", "rr_calf"),
            "power_system": ("battery_percent", "pack_voltage_v", "total_current_a"),
            "body_imu": ("imu_roll_deg", "imu_pitch_deg", "imu_yaw_deg"),
            "communication": ("signal_strength_percent",),
            "mission_state": ("robot_mode", "status", "event", "waypoint"),
        },
    ),
    "mobile_robot": RobotProfile(
        key="mobile_robot",
        display_name="Mobile Robot",
        robot_type="mobile_robot",
        description="Ground mobile robot profile for wheeled or tracked platforms with route, power, drive, and localization diagnostics.",
        required_fields=(
            "mission_time_s",
            "battery_percent",
            "status",
        ),
        optional_fields=(
            "x_m",
            "y_m",
            "left_wheel_current_a",
            "right_wheel_current_a",
            "left_wheel_speed_mps",
            "right_wheel_speed_mps",
            "obstacle_distance_m",
            "localization_quality",
            "signal_strength_percent",
            "waypoint",
            "event",
        ),
        diagnostic_categories=(
            "battery",
            "current",
            "wheel_slip",
            "stalled_motion",
            "localization",
            "obstacle_proximity",
            "communication",
            "mission_risk",
        ),
        supported_metrics=(
            "battery_percent",
            "left_wheel_current_a",
            "right_wheel_current_a",
            "wheel_speed",
            "route_efficiency",
            "obstacle_distance_m",
            "localization_quality",
            "signal_strength_percent",
            "event_count",
        ),
        component_groups={
            "left_drive": ("left_wheel_current_a", "left_wheel_speed_mps"),
            "right_drive": ("right_wheel_current_a", "right_wheel_speed_mps"),
            "power_system": ("battery_percent", "pack_voltage_v", "total_current_a"),
            "localization": ("x_m", "y_m", "localization_quality"),
            "communication": ("signal_strength_percent",),
            "mission_state": ("status", "event", "waypoint"),
        },
    ),
    "manipulator": RobotProfile(
        key="manipulator",
        display_name="Manipulator",
        robot_type="manipulator",
        description="Robotic arm profile for actuator, motion tracking, end-effector, and cycle diagnostics.",
        required_fields=(
            "mission_time_s",
            "status",
        ),
        optional_fields=(
            "joint_position_rad",
            "joint_velocity_rad_s",
            "joint_torque_nm",
            "joint_current_a",
            "joint_temp_c",
            "position_error_rad",
            "end_effector_state",
            "cycle_id",
            "cycle_status",
            "event",
        ),
        diagnostic_categories=(
            "thermal",
            "current",
            "torque",
            "position_error",
            "motion_tracking",
            "collision_risk",
            "cycle_failure",
            "mission_risk",
        ),
        supported_metrics=(
            "joint_temperature",
            "joint_current",
            "joint_torque",
            "joint_position",
            "position_error",
            "motion_tracking_error",
            "end_effector_state",
            "cycle_failure_count",
            "event_count",
        ),
        component_groups={
            "arm_joints": (
                "joint_position_rad",
                "joint_velocity_rad_s",
                "joint_torque_nm",
                "joint_current_a",
                "joint_temp_c",
            ),
            "end_effector": ("end_effector_state",),
            "power_system": ("battery_percent", "pack_voltage_v", "total_current_a"),
            "controller_state": ("position_error_rad", "cycle_status"),
            "mission_state": ("status", "event", "cycle_id"),
        },
    ),
    "generic_robot": RobotProfile(
        key="generic_robot",
        display_name="Generic Robot",
        robot_type="generic_robot",
        description="Fallback profile for broad robot telemetry diagnostics when a specific robot profile is not available.",
        required_fields=(
            "mission_time_s",
            "status",
        ),
        optional_fields=(
            "timestamp",
            "battery_percent",
            "temperature_c",
            "current_a",
            "signal_strength_percent",
            "event",
        ),
        diagnostic_categories=(
            "battery",
            "thermal",
            "current",
            "communication",
            "status",
            "mission_risk",
        ),
        supported_metrics=(
            "battery_percent",
            "temperature_c",
            "current_a",
            "signal_strength_percent",
            "status",
            "event_count",
        ),
        component_groups={
            "power_system": ("battery_percent", "current_a"),
            "thermal_system": ("temperature_c",),
            "communication": ("signal_strength_percent",),
            "mission_state": ("status", "event"),
        },
    ),
}


def list_robot_profiles() -> tuple[RobotProfile, ...]:
    return tuple(_PROFILES.values())


def list_robot_profile_keys() -> tuple[str, ...]:
    return tuple(_PROFILES.keys())


def robot_profile_exists(profile_key: str) -> bool:
    return profile_key in _PROFILES


def get_robot_profile(profile_key: str) -> RobotProfile:
    try:
        return _PROFILES[profile_key]
    except KeyError as exc:
        valid_keys = ", ".join(list_robot_profile_keys())
        raise ValueError(f"Unknown robot profile '{profile_key}'. Valid profiles: {valid_keys}") from exc
