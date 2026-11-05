"""Small durable learning store for the local MVP.

The data model deliberately mirrors a future database schema: paths, lessons,
progress, quiz attempts, bookmarks and notes are separate records.  It is kept
in a JSON file so Phase 2 remains runnable without external infrastructure.
"""
from __future__ import annotations
import json, math
from pathlib import Path
from threading import Lock
from scientific.orbit import circular_orbit_metrics

STORE = Path(__file__).parents[1] / 'data' / 'learning-progress.json'
LOCK = Lock()
PATHS = [
 {'id':'foundations','title':'Foundations of Space Science','difficulty':'Beginner','duration':'4h 20m','description':'Build an intuition for gravity, motion, and the language of spaceflight.','objectives':['Describe orbit as free-fall','Use Newton’s laws in space','Interpret Kepler’s laws'],'lessons':['intro-space','gravity-orbits','orbital-velocity','kepler-laws','newton-space']},
 {'id':'orbital-mechanics','title':'Orbital Mechanics','difficulty':'Intermediate','duration':'7h 10m','description':'Model circular and elliptical trajectories from first principles.','objectives':['Calculate circular velocity','Compare conic orbits','Reason about transfers'],'prerequisites':['foundations'],'lessons':['circular-orbits','elliptical-orbits','escape-velocity','period','inclination','hohmann']},
 {'id':'satellites','title':'Satellites & Spacecraft','difficulty':'Beginner','duration':'3h 45m','description':'Explore satellite missions, spacecraft systems, and Earth observation.','objectives':['Identify spacecraft subsystems','Match missions to orbits'],'lessons':['satellite-basics','subsystems','earth-observation']},
 {'id':'rocket-science','title':'Rocket Science','difficulty':'Intermediate','duration':'5h 30m','description':'Learn thrust, delta-v, and the rocket equation.','objectives':['Apply Tsiolkovsky’s equation','Explain specific impulse'],'lessons':['rocket-fundamentals','thrust','delta-v','rocket-equation']},
 {'id':'advanced','title':'Advanced Space Science','difficulty':'Advanced','duration':'6h 40m','description':'A first look at mission design and astrodynamics.','objectives':['Explain Lagrange points','Frame an interplanetary transfer'],'prerequisites':['orbital-mechanics'],'lessons':['lagrange','interplanetary','perturbations','mission-design']}
]
LESSONS = {
 'orbital-velocity': {'id':'orbital-velocity','path_id':'foundations','title':'Orbital Velocity','duration':'24 min','level':'Foundations','summary':'Why a satellite falls around Earth instead of down to it.','sections':[{'heading':'Orbit is continuous free-fall','body':'Gravity accelerates a satellite toward Earth. Its sideways velocity makes the surface curve away at the same rate, so the satellite continually falls around the planet.'},{'heading':'The circular-orbit relationship','body':'For a circular orbit, gravity provides the centripetal acceleration. Setting GM/r² equal to v²/r gives the expression below.'},{'heading':'Altitude changes speed','body':'A higher orbit has a larger radius r and therefore a lower circular speed. It also has a longer period.'}], 'equation':'v = √(GM / r)', 'variables':[('v','orbital velocity'),('G','gravitational constant'),('M','Earth mass'),('r','distance from Earth’s centre')], 'quiz':{'id':'orbital-velocity-check','question':'At a higher circular orbit, the required orbital velocity is…','options':['higher because gravity is weaker','lower because the orbital radius is larger','unchanged for all circular orbits','zero at geostationary altitude'],'answer':1,'explanation':'v = √(μ/r): as r increases, circular speed decreases. The period increases at the same time.'}},
 'gravity-orbits': {'id':'gravity-orbits','path_id':'foundations','title':'Gravity and Orbital Motion','duration':'18 min','level':'Foundations','summary':'Gravity is the force that bends an inertial path into an orbit.','sections':[{'heading':'A universal interaction','body':'Every mass attracts every other mass. Around Earth, the acceleration decreases with the square of distance.'},{'heading':'From falling to orbiting','body':'Increase horizontal velocity and a falling object travels farther before reaching the ground. At orbital speed it continually misses Earth.'}], 'equation':'a = μ / r²','variables':[('a','gravitational acceleration'),('μ','Earth gravitational parameter'),('r','distance from Earth centre')]},
 'kepler-laws': {'id':'kepler-laws','path_id':'foundations','title':'Kepler’s Laws','duration':'22 min','level':'Foundations','summary':'Three concise rules that describe ideal planetary motion.','sections':[{'heading':'First law','body':'Bound two-body orbits are ellipses with the primary body at one focus.'},{'heading':'Third law','body':'The square of the period is proportional to the cube of the semi-major axis.'}], 'equation':'T² ∝ a³','variables':[('T','orbital period'),('a','semi-major axis')]}
}
def _default(): return {'completed':[],'bookmarks':[],'notes':{},'attempts':{},'current_lesson':'orbital-velocity','seconds':0}
def read():
 with LOCK:
  if not STORE.exists(): return _default()
  try: return {**_default(),**json.loads(STORE.read_text())}
  except json.JSONDecodeError: return _default()
def write(data):
 with LOCK:
  STORE.parent.mkdir(exist_ok=True); STORE.write_text(json.dumps(data,indent=2)); return data
def progress():
 s=read(); total=sum(len(p['lessons']) for p in PATHS); return {**s,'completed_count':len(s['completed']),'total_lessons':total,'paths':[ {**p,'completed_count':sum(x in s['completed'] for x in p['lessons'])} for p in PATHS]}
def lesson(ident):
 if ident in LESSONS:return LESSONS[ident]
 # Other path lessons are deliberately concise, but are genuine navigable records.
 for p in PATHS:
  if ident in p['lessons']: return {'id':ident,'path_id':p['id'],'title':ident.replace('-',' ').title(),'duration':'16 min','level':p['difficulty'],'summary':'A structured ASTRA Learn lesson.','sections':[{'heading':'Lesson briefing','body':'This module is being prepared as an interactive scientific lesson.'}]}
 return None
def velocity(altitude_km):
 m=circular_orbit_metrics(altitude_km)
 return {'altitude_km':altitude_km,'radius_km':m['radius_m']/1000,'velocity_kms':m['velocity_mps']/1000,'escape_velocity_kms':m['escape_velocity_mps']/1000,'period_min':m['period_s']/60,'gravity_mps2':m['gravity_mps2'],'frame':'Idealized circular Earth-centered inertial orbit.'}
