from ..backend import BackendBase, CasadiBackend
from ..utils.arrays import ArrayLike
import casadi as cs

from ..model._base import Energy, CoM, ModelBase
from ._model import Model, Regressors

from ..model._body import Body
from ..model.functional import FunctionalBody
from typing import List, Dict


class Functional(ModelBase):
    def __init__(self, backend: BackendBase):
        assert isinstance(
            backend, CasadiBackend
        ), "Symbolic robot only works with Casadi backend"
        self._backend = backend

        self.__robot = Model(backend)

        # instances we want to cache
        self.__com = None
        self.__energy = None

    @property
    def expression_model(self):
        return self.__robot

    @property
    def regressors(
        self,
        q: ArrayLike | None = None,
        v: ArrayLike | None = None,
        dv: ArrayLike | None = None,
    ) -> Regressors:
        regrs = self.__robot.regressors(q, v, dv)

        return Regressors(
            torque=cs.Function(
                "torque_regressor",
                [self.q, self.v, self.dv],
                [regrs.torque],
                ["q", "v", "dv"],
                ["torque_regressor"],
            ),
            kinetic=cs.Function(
                "kinetic_regressor",
                [self.q, self.v],
                [regrs.kinetic],
                ["q", "v"],
                ["kinetic_regressor"],
            ),
            potential=cs.Function(
                "potential_regressor",
                [self.q],
                [regrs.potential],
                ["q"],
                ["potential_regressor"],
            ),
            momentum=cs.Function(
                "momentum_regressor",
                [self.q, self.v],
                [*regrs.momentum],
                ["q", "v"],
                ["momentum_regressor", "partial_lagrangian_configuration"],
            ),
        )

    @property
    def parameters(self) -> ArrayLike:
        return self.__robot._parameters

    @property
    def q(self) -> ArrayLike:
        return self.__robot.q

    @property
    def v(self) -> ArrayLike:
        return self.__robot.v

    @property
    def dv(self) -> ArrayLike:
        return self.__robot.dv

    @property
    def qfrc_u(self) -> ArrayLike:
        return self.__robot.qfrc_u

    @property
    def backend(self) -> BackendBase:
        return self.__robot.backend

    @property
    def nq(self) -> int:
        return self.__robot.backend.nq

    @property
    def nv(self) -> int:
        return self.__robot.backend.nv

    @property
    def nu(self) -> int:
        return self.__robot.nu

    @property
    def nbodies(self) -> int:
        return self.__robot.backend.nbodies

    @property
    def q_min(self) -> ArrayLike:
        return self.__robot.backend.q_min

    @property
    def q_max(self) -> ArrayLike:
        return self.__robot.backend.q_max

    @property
    def joint_names(self) -> List[str]:
        return self.__robot.backend.joint_names

    @property
    def bodies(self) -> Dict[str, FunctionalBody]:
        # TODO: probably we should map each element to FunctionalBody too
        return self.__robot.bodies

    def add_body(self, bodies_names: List[str] | Dict[str, str]):
        return self.__robot.add_body(bodies_names, Body)

    def body(self, name: str) -> FunctionalBody:
        return FunctionalBody.from_body(self.__robot.body(name))

    # @property
    # def state_space(self):
    #     return FunctionalStateSpace.from_space(self.__robot.state_space)

    @property
    def selector(self):
        return self.__robot.selector

    def joint_id(self, name: str) -> int:
        return self.__robot.joint_id(name)

    @property
    def contact_forces(self) -> List[ArrayLike]:
        return self.__robot.contact_forces

    @property
    def contact_names(self) -> List[str]:
        return self.__robot.contact_names

    def update_selector(
        self,
        matrix: ArrayLike | None = None,
        passive_joints: List[str | int] | None = None,
    ):
        self.__robot.update_selector(matrix, passive_joints)

    @property
    def gravity(self) -> cs.Function:
        return cs.Function(
            "gravity",
            [self.q, self.__robot.parameters],
            [self.__robot.gravity(self.q)],
            ["q", "parameters"],
            ["gravity"],
        )

    @property
    def com(self) -> CoM:
        if self.__com is not None:
            return self.__com

        supercom = self.__robot.com(self.q, self.v, self.dv)

        self.__com = CoM(
            position=cs.Function(
                "com_position",
                [self.q],
                [supercom.position],
                ["q"],
                ["com_position"],
            ),
            jacobian=cs.Function(
                "com_jacobian",
                [self.q],
                [supercom.jacobian],
                ["q"],
                ["com_jacobian"],
            ),
            velocity=cs.Function(
                "com_velocity",
                [self.q, self.v],
                [supercom.velocity],
                ["q", "v"],
                ["com_velocity"],
            ),
            acceleration=cs.Function(
                "com_acceleration",
                [self.q, self.v, self.dv],
                [supercom.acceleration],
                ["q", "v", "dv"],
                ["com_acceleration"],
            ),
            jacobian_dt=cs.Function(
                "com_jacobian_dt",
                [self.q, self.v],
                [supercom.jacobian_dt],
                ["q", "v"],
                ["com_jacobian_dt"],
            ),
        )
        return self.__com

    @property
    def energy(self) -> Energy:
        if self.__energy is not None:
            return self.__energy

        superenergy = self.__robot.energy(self.q, self.v)

        self.__energy = Energy(
            kinetic=cs.Function(
                "kinetic_energy",
                [self.q, self.v, self.__robot.parameters],
                [superenergy.kinetic],
                ["q", "v", "parameters"],
                ["kinetic_energy"],
            ),
            potential=cs.Function(
                "potential_energy",
                [self.q, self.__robot.parameters],
                [superenergy.potential],
                ["q", "parameters"],
                ["potential_energy"],
            ),
        )
        return self.__energy

    @property
    def inertia(self) -> ArrayLike:
        return cs.Function(
            "inertia",
            [self.q, self.__robot.parameters],
            [self.__robot.inertia(self.q)],
            ["q", "parameters"],
            ["inertia"],
        )

    @property
    def coriolis(self) -> ArrayLike:
        return cs.Function(
            "coriolis",
            [self.q, self.v, self.__robot.parameters],
            [self.__robot.coriolis(self.q, self.v)],
            ["q", "v", "parameters"],
            ["coriolis"],
        )

    @property
    def bias_force(self) -> ArrayLike:
        return cs.Function(
            "bias_force",
            [self.q, self.v, self.__robot.parameters],
            [self.__robot.bias_force(self.q, self.v)],
            ["q", "v", "parameters"],
            ["bias_force"],
        )

    @property
    def momentum(self) -> ArrayLike:
        return cs.Function(
            "momentum",
            [self.q, self.v, self.__robot.parameters],
            [self.__robot.momentum(self.q, self.v)],
            ["q", "v"],
            ["momentum"],
        )

    @property
    def lagrangian(self) -> ArrayLike:
        return cs.Function(
            "lagrangian",
            [self.q, self.v, self.__robot.parameters],
            [self.__robot.lagrangian(self.q, self.v)],
            ["q", "v", "parameters"],
            ["lagrangian"],
        )

    @property
    def contact_qforce(self) -> ArrayLike:
        return cs.Function(
            "contact_qforce",
            [self.q, *self.__robot.contact_forces],
            [self.__robot.contact_qforce],
            ["q", *self.contact_names],
            ["contact_qforce"],
        )

    @property
    def coriolis_matrix(self) -> ArrayLike:
        return cs.Function(
            "coriolis_matrix",
            [self.q, self.v, self.__robot.parameters],
            [self.__robot.coriolis_matrix(self.q, self.v)],
            ["q", "v", "parameters"],
            ["coriolis_matrix"],
        )

    @property
    def forward_dynamics(self) -> ArrayLike:
        return cs.Function(
            "forward_dynamics",
            [
                self.q,
                self.v,
                self.qfrc_u,
                *self.contact_forces,
                self.__robot.parameters,
            ],
            [self.__robot.forward_dynamics(self.q, self.v, self.qfrc_u)],
            ["q", "v", "tau", *self.contact_names, "parameters"],
            ["dv"],
        )

    @property
    def inverse_dynamics(self) -> ArrayLike:
        return cs.Function(
            "inverse_dynamics",
            [
                self.q,
                self.v,
                self.dv,
                *self.__robot.contact_forces,
                self.__robot.parameters,
            ],
            [self.__robot.inverse_dynamics(self.q, self.v, self.dv)],
            ["q", "v", "dv", *self.contact_names, "parameters"],
            ["tau"],
        )

    @property
    def centroidal_dynamics(
        self,
        q: ArrayLike | None = None,
        v: ArrayLike | None = None,
        dv: ArrayLike | None = None,
    ):
        raise NotImplementedError

    def update(
        self,
        q: ArrayLike,
        v: ArrayLike,
        dv: ArrayLike | None = None,
        u: ArrayLike | None = None,
    ) -> ArrayLike:
        # dummy implementation to satisfy base class
        return
