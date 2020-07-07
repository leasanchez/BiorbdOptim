import biorbd
import pickle
from time import time

from biorbd_optim import (
    OptimalControlProgram,
    DynamicsType,
    DynamicsTypeList,
    BoundsList,
    QAndQDotBounds,
    InitialConditionsList,
    ShowResult,
    Objective,
    ObjectiveList,
)


def prepare_ocp(biorbd_model_path, final_time, number_shooting_points, nb_threads, use_SX=False):
    # --- Options --- #
    biorbd_model = biorbd.Model(biorbd_model_path)
    torque_min, torque_max, torque_init = -100, 100, 0
    n_q = biorbd_model.nbQ()
    n_qdot = biorbd_model.nbQdot()
    n_tau = biorbd_model.nbGeneralizedTorque()

    # Add objective functions
    objective_functions = ObjectiveList()
    objective_functions.add(Objective.Lagrange.MINIMIZE_TORQUE_DERIVATIVE)

    # Dynamics
    dynamics = DynamicsTypeList()
    dynamics.add(DynamicsType.TORQUE_DRIVEN)

    # Path constraint
    x_bounds = BoundsList()
    x_bounds.add(QAndQDotBounds(biorbd_model))
    x_bounds[0].min[:, [0, -1]] = 0
    x_bounds[0].max[:, [0, -1]] = 0
    x_bounds[0].min[1, -1] = 3.14
    x_bounds[0].max[1, -1] = 3.14

    # Initial guess
    x_init = InitialConditionsList()
    x_init.add([0] * (n_q + n_qdot))

    # Define control path constraint
    u_bounds = BoundsList()
    u_bounds.add([[torque_min] * n_tau, [torque_max] * n_tau])
    u_bounds[0].min[n_tau - 1, :] = 0
    u_bounds[0].max[n_tau - 1, :] = 0

    u_init = InitialConditionsList()
    u_init.add([torque_init] * n_tau)

    # ------------- #

    return OptimalControlProgram(
        biorbd_model,
        dynamics,
        number_shooting_points,
        final_time,
        x_init,
        u_init,
        x_bounds,
        u_bounds,
        objective_functions,
        nb_threads=nb_threads,
        use_SX=use_SX,
    )


if __name__ == "__main__":
    ocp = prepare_ocp(biorbd_model_path="pendulum.bioMod", final_time=3, number_shooting_points=100, nb_threads=4)

    # --- Solve the program --- #
    tic = time()
    sol, sol_iterations = ocp.solve(show_online_optim=True, return_iterations=True)
    toc = time() - tic
    print(f"Time to solve : {toc}sec")

    # --- Access to all iterations  --- #
    nb_iter = len(sol_iterations)
    third_iteration = sol_iterations[2]

    # --- Save result of get_data --- #
    ocp.save_get_data(sol, "pendulum.bob", sol_iterations)  # you don't have to specify the extension ".bob"

    # --- Load result of get_data --- #
    with open("pendulum.bob", "rb") as file:
        data = pickle.load(file)

    # --- Save the optimal control program and the solution --- #
    ocp.save(sol, "pendulum.bo")  # you don't have to specify the extension ".bo"

    # --- Load the optimal control program and the solution --- #
    ocp_load, sol_load = OptimalControlProgram.load("pendulum.bo")

    # --- Show results --- #
    result = ShowResult(ocp_load, sol_load)
    result.animate()
