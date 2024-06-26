# -*- coding: utf-8 -*-
"""02_go2_ik_manopt.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nTsQ4VzzYMG5oxXJu0TpYaPEKmkV09ki
"""

import numpy as np
from darli.model import Functional
from darli.robots import quadruped
from darli.backend import CasadiBackend, JointType
from darli.backend.liecasadi.so3 import SO3

import casadi as cs

print("hello")

#!pip3 install robot_descriptions

#%%capture
# !pip3 install robot_descriptions
from robot_descriptions import go2_description, go2_mj_description
# from robot_descriptions import a1_description, a1_mj_description

#!pip install mujoco

#!pip install mujoco

#!pip3 install mujoco_simulator

# Commented out IPython magic to ensure Python compatibility.
import mujoco
import mediapy as media
import numpy as np
import mujoco.viewer


# %env MUJOCO_GL=egl
renderer = None

#!pip install mediapy


model = quadruped(Functional, CasadiBackend,
                  go2_description.URDF_PATH,
                  foots={'fl': "FL_foot",
                         'fr': "FR_foot",
                         'rl': "RL_foot",
                         'rr': "RR_foot"},
                  root_joint=JointType.FREE_FLYER)

model.nq

model.bodies.keys()

"""Define the variables in tangent space and get the configuration via exponential:"""

opti_problem = cs.Opti()
dq = opti_problem.variable(model.nv)

q0 = opti_problem.parameter(model.nq)

q = model.backend.integrate_configuration(q0, dq)

for body in model.bodies.values():
    name = body.name
    if name != 'torso':
        initial_foot_pos = model.body(name).position(q0)
        initial_foot_pos[2] = 0
        opti_problem.subject_to(model.body(name).position(q) == initial_foot_pos)

torso_pos = q[:3]
torso_xyzw = q[3:7]

desired_pos = opti_problem.parameter(3)
desired_xyzw = opti_problem.parameter(4)

so3_error = SO3(xyzw=torso_xyzw).distance(SO3(xyzw = desired_xyzw))
pos_cost = cs.sumsqr(torso_pos - desired_pos)
so3_cost = 0.1*so3_error

cost = pos_cost + so3_cost #+ gravity_cost
opti_problem.minimize(cost)
opti_problem.subject_to(opti_problem.bounded(model.q_min, q[7:], model.q_max))
opti_problem.solver('ipopt')

pos_des = [0.0, 0.0, 0.3]
xyzw_des = SO3.qy(-0.3).xyzw

q_init = np.zeros(model.nq)
q_init[6] = 1
opti_problem.set_initial(dq, np.zeros(model.nv))
opti_problem.set_value(q0,q_init)
opti_problem.set_value(desired_pos,pos_des)
opti_problem.set_value(desired_xyzw, xyzw_des)

#!export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(python3 -m cmeel lib)
#!echo $LD_LIBRARY_PATH

print("Try")

opti_problem.solve()

dq_opt = opti_problem.value(dq)
# dq_opt

q_opt = opti_problem.value(q)
# q_opt

# q_opt[:3]

# ren.set_state(q_opt)

# q_opt[3:7]

# xyzw_des

pos_des = [0.0, 0.0, 0.28]
xyzw_des = [0.0, 0.0, 0.0, 1.0]

opti_problem.set_initial(dq, dq_opt)
opti_problem.set_value(q0,q_opt)
opti_problem.set_value(desired_pos, pos_des)
opti_problem.set_value(desired_xyzw, xyzw_des)

opti_problem.solve()

q_opt = opti_problem.value(q)
# q_opt

# q_opt[:3]

# q_opt[3:7]

cost = pos_cost + 0.5*so3_cost + 0.0001*cs.sumsqr(dq)
opti_problem.minimize(cost)
opti_problem.solver(
            "ipopt",
            {
                "ipopt.print_level": 0,
                # 'ipopt.max_iter': 3,
                "print_time": 0,
                "ipopt.warm_start_init_point": "yes"
            },
        )

# opti_problem.solver('sqpmethod')
from time import perf_counter, sleep
import time 

SIMULATION_TIME = 10

with mujoco.viewer.launch_passive(model, data) as viewer:
    start = time.time()


    xyzw_des = [0,0,0,1]

    while viewer.is_running() and time.time() - start < SIMULATION_TIME:
            step_start = time.time()

    for j in range(2):
        for i in range(600):
            t1 = perf_counter()
            coordinate = 0.08*np.sin(2*np.pi*i/100)
            if i >=0:
                pos_des = [coordinate, 0.0, 0.3]
            if i >=100:
                pos_des = [0, coordinate, 0.3]
            if i >=200:
                pos_des = [0, 0.0, 0.3 + coordinate]
            if i >=300:
                pos_des = [0, 0.0, 0.3]
                xyzw_des = SO3.qx(6*coordinate).xyzw
            if i >=400:
                xyzw_des = SO3.qy(6*coordinate).xyzw
            if i >=500:
                xyzw_des = SO3.qz(6*coordinate).xyzw


            opti_problem.set_value(desired_pos,pos_des)
            opti_problem.set_value(desired_xyzw,xyzw_des)
            opti_problem.set_initial(dq,dq_opt)
            try:
                sol = opti_problem.solve()
                dq_opt = opti_problem.value(dq)
                q_opt = opti_problem.value(q)
            except Exception as e:
                dq_opt = opti_problem.debug.value(dq)
                q_opt = opti_problem.debug.value(q)

            dq_opt = opti_problem.value(dq)
            q_opt = opti_problem.value(q)
            # print(q_opt)

            t2 = perf_counter()
            print(1000*(t2 - t1))
            # ren.set_state(q_opt)

            # ren.markers[0](position=q_opt[:3].copy(),
            #                     color=[1, 0, 0, 0.5],
            #                     size=0.02)

            # ren.markers[1](position=np.array(pos_des).copy(),
            #                     color=[0, 0, 1, 0.5],
            #                     size=0.022)
            sleep(0.01)
