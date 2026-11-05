"""Numerical two-body propagation in the Earth-centered inertial (ECI) frame."""
from __future__ import annotations
import math
import numpy as np
from scipy.integrate import solve_ivp

MU_EARTH = 3.986004418e14  # m^3 / s^2
R_EARTH = 6_378_137.0  # m (equatorial radius)

class OrbitInputError(ValueError): pass

def circular_orbit_metrics(altitude_km: float) -> dict:
    """Analytical circular-orbit reference values; public values use km/s and minutes."""
    if not 100 <= altitude_km <= 100_000: raise OrbitInputError('Altitude must be between 100 and 100,000 km.')
    radius=R_EARTH+altitude_km*1000
    velocity=math.sqrt(MU_EARTH/radius); escape=math.sqrt(2*MU_EARTH/radius)
    period=2*math.pi*math.sqrt(radius**3/MU_EARTH); gravity=MU_EARTH/radius**2
    return {'radius_m':radius,'velocity_mps':velocity,'escape_velocity_mps':escape,'period_s':period,'gravity_mps2':gravity,'specific_energy_jkg':-MU_EARTH/(2*radius),'angular_momentum_m2s':math.sqrt(MU_EARTH*radius)}

def _derivative(_: float, y: np.ndarray) -> np.ndarray:
    r, v = y[:3], y[3:]
    radius = float(np.linalg.norm(r))
    return np.concatenate((v, -MU_EARTH * r / radius**3))

def validate(config: dict) -> None:
    if not 100 <= config['altitude_km'] <= 100_000: raise OrbitInputError('Altitude must be between 100 and 100,000 km.')
    if not 0 <= config['inclination_deg'] <= 180: raise OrbitInputError('Inclination must be between 0 and 180 degrees.')
    if not 1 <= config['duration_s'] <= 604800: raise OrbitInputError('Duration must be between 1 second and 7 days.')
    if not 1 <= config['time_step_s'] <= 3600: raise OrbitInputError('Time step must be between 1 and 3,600 seconds.')
    if not 1_000 <= config['velocity_kms'] * 1000 <= 20_000: raise OrbitInputError('Velocity must be between 1 and 20 km/s.')

def propagate(config: dict) -> dict:
    validate(config)
    radius = R_EARTH + config['altitude_km'] * 1000
    inc = math.radians(config['inclination_deg'])
    velocity = config['velocity_kms'] * 1000
    y0 = np.array([radius, 0., 0., 0., velocity * math.cos(inc), velocity * math.sin(inc)])
    duration, dt = config['duration_s'], config['time_step_s']
    times = np.arange(0, duration + dt, dt, dtype=float); times[-1] = duration
    sol = solve_ivp(_derivative, (0, duration), y0, t_eval=times, rtol=1e-9, atol=1e-4, method='DOP853')
    if not sol.success or not np.all(np.isfinite(sol.y)): raise RuntimeError('Numerical propagation failed.')
    pos, vel = sol.y[:3].T, sol.y[3:].T
    radii = np.linalg.norm(pos, axis=1); speeds = np.linalg.norm(vel, axis=1)
    altitude = radii - R_EARTH
    energy = speeds**2 / 2 - MU_EARTH / radii
    hvec = np.cross(pos, vel); h = np.linalg.norm(hvec, axis=1)
    evec = np.cross(vel, hvec) / MU_EARTH - pos / radii[:, None]; ecc = np.linalg.norm(evec, axis=1)
    semimajor = -MU_EARTH / (2 * energy[0])
    period = 2 * math.pi * math.sqrt(semimajor**3 / MU_EARTH) if energy[0] < 0 else None
    return {
      'frame': 'Earth-centered inertial (ECI), ideal point-mass Earth; SI units internally.',
      'initial_state': {'position_m': pos[0].tolist(), 'velocity_mps': vel[0].tolist()},
      'final_state': {'position_m': pos[-1].tolist(), 'velocity_mps': vel[-1].tolist()},
      'metrics': {'orbital_period_s': period, 'current_altitude_km': float(altitude[-1]/1000), 'orbital_velocity_kms': float(speeds[-1]/1000), 'escape_velocity_kms':float(math.sqrt(2*MU_EARTH/radii[-1])/1000), 'gravitational_acceleration_mps2':float(MU_EARTH/radii[-1]**2), 'semi_major_axis_km':float(semimajor/1000), 'eccentricity': float(ecc[0]), 'specific_energy_jkg': float(energy[0]), 'angular_momentum_m2s': float(h[0]), 'simulation_duration_s': duration},
      'series': {'time_s': times.tolist(), 'altitude_km': (altitude/1000).tolist(), 'velocity_kms': (speeds/1000).tolist(), 'energy_jkg': energy.tolist(), 'x_km': (pos[:,0]/1000).tolist(), 'y_km': (pos[:,1]/1000).tolist(), 'z_km': (pos[:,2]/1000).tolist()},
      'validation': {'energy_relative_drift': float(abs((energy[-1]-energy[0])/energy[0])), 'angular_momentum_relative_drift': float(abs((h[-1]-h[0])/h[0]))}
    }
