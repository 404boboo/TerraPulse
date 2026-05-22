# TerraPulse

TerraPulse is Quadruped Mission Replay, Route Risk Scoring, and Field Incident Analysis

It replays robot missions, scores route risk, detects operational incidents, and generates engineer-ready reports from exported, simulated, or real telemetry.

The project starts with CSV mission exports and is designed to evolve toward ROS2, Gazebo, NVIDIA Isaac Sim, CAN bus telemetry, real robot hardware, and ML-based risk prediction.

## Core Goals

- Replay quadruped inspection missions
- Visualize robot telemetry over time
- Score operational route risk
- Detect mission incidents and failures
- Generate engineering incident reports
- Support simulated and real robotics telemetry
- Prepare structured datasets for future ML prediction

## Planned Tech Stack

### Initial MVP
- Python
- Streamlit
- Pandas
- Plotly
- Pytest

### Robotics Integration
- ROS2
- Gazebo
- NVIDIA Isaac Sim
- MCAP / rosbag support
- CAN bus telemetry adapters

### Future ML Stack
- Scikit-learn
- XGBoost
- PyTorch 