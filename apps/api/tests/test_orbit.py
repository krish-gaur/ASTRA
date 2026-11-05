import math
import pytest
from scientific.orbit import propagate, MU_EARTH, R_EARTH, OrbitInputError
from scientific.orbit import circular_orbit_metrics
def cfg():
 r=R_EARTH+400000; return dict(altitude_km=400,inclination_deg=51.6,velocity_kms=math.sqrt(MU_EARTH/r)/1000,duration_s=5400,time_step_s=20)
def test_circular_orbit_and_conservation():
 x=propagate(cfg()); assert x['metrics']['eccentricity'] < 1e-5; assert x['validation']['energy_relative_drift'] < 1e-7; assert x['validation']['angular_momentum_relative_drift'] < 1e-7
def test_kepler_period():
 x=propagate(cfg()); r=R_EARTH+400000; assert abs(x['metrics']['orbital_period_s']-2*math.pi*math.sqrt(r**3/MU_EARTH)) < .1
def test_invalid():
 c=cfg(); c['altitude_km']=2; 
 with pytest.raises(OrbitInputError): propagate(c)
def test_analytical_circular_relationships():
 m=circular_orbit_metrics(400)
 assert abs(m['velocity_mps']-7668.56)<1
 assert abs(m['escape_velocity_mps']/m['velocity_mps']-math.sqrt(2))<1e-12
 assert abs(m['period_s']-5553.6)<2
