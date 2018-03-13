from __future__ import division
import numpy as np
import fidimag.extensions.clib as clib
import fidimag.common.helper as helper
import fidimag.common.constant as const

from .atomistic_driver import AtomisticDriver


class SteepestDescent(AtomisticDriver):
    """

    This class is the driver to minimise a system using a Steepest Descent
    algorithm



    This class inherits common methods to evolve the system using CVODE, from
    the micro_driver.AtomisticDriver class. Arrays with the system information
    are taken as references from the main micromagnetic Simulation class

    """

    def __init__(self, mesh, spin, mu_s, mu_s_inv, field, pins,
                 interactions,
                 name,
                 data_saver,
                 use_jac=False,
                 integrator=None
                 ):

        # self.mesh = mesh
        # self.spin = spin
        # self.mu_s mu_s
        # self._mu_s_inv = mu_s_inv
        # self.field = field
        # self.pins = pins
        # self.interactions = interactions
        # self.name = name
        # self.data_saver = data_saver

        # Inherit from the driver class
        super(SteepestDescent, self).__init__(mesh, spin, mu_s, mu_s_inv, field,
                                              pins, interactions, name,
                                              data_saver,
                                              use_jac=use_jac,
                                              integrator=integrator
                                              )

        self.mxH = np.zeros_like(self.field)
        self.mxmxH = np.zeros_like(self.field)
        self.mxmxH_last = np.zeros_like(self.field)
        self.t = 1e-4
        self.tau = 1e-4 * np.ones(len(self.spin) // 3)

        # self.set_options()

    def get_time_step(self):
        ds = (self.spin - self.spin_last).reshape(-1, 3)
        dy = (self.mxmxH - self.mxmxH_last).reshape(-1, 3)

        print(ds)
        print(dy)

        if self.counter % 2 == 0:
            num = np.sum(ds * ds, axis=1)
            den = np.sum(ds * dy, axis=1)
        else:
            num = np.sum(ds * dy, axis=1)
            den = np.sum(dy * dy, axis=1)

        # Denominators equal to zero are set to 1e-4
        tau = 1e-4 * np.ones_like(num)
        tau[den != 0] = num[den != 0] / den[den != 0]

        print(tau)

        return tau

    def compute_rhs(self, tau):
        self.mxH.shape = (-1, 3)
        self.mxmxH.shape = (-1, 3)
        self.spin.shape = (-1, 3)

        mxH_sq_norm = np.sum(self.mxH ** 2, axis=1)
        factor_plus = 4 + (tau ** 2) * mxH_sq_norm
        factor_minus = 4 - (tau ** 2) * mxH_sq_norm

        self.spin = factor_minus[:, np.newaxis] * self.spin - 4 * (tau[:, np.newaxis] * self.mxmxH)
        self.spin = self.spin / factor_plus[:, np.newaxis]

        self.mxH.shape = (-1,)
        self.mxmxH.shape = (-1,)
        self.spin.shape = (-1,)

    def field_cross_product(self, a, b):
        aXb = np.cross(a.reshape(-1, 3), b.reshape(-1, 3))
        return aXb.reshape(-1,)

    def run_step(self):

        self.mxmxH_last[:] = self.mxmxH[:]
        self.update_effective_field()
        self.mxH[:] = self.field_cross_product(self.spin, self.field)[:]
        self.mxmxH[:] = self.field_cross_product(self.spin, self.mxH)[:]

        # ---------------------------------------------------------------------
        # self.tau = self.get_time_step()
        ds = (self.spin - self.spin_last).reshape(-1, 3)
        dy = (self.mxmxH - self.mxmxH_last).reshape(-1, 3)

        if self.counter % 2 == 0:
            num = np.sum(ds * ds, axis=1)
            den = np.sum(ds * dy, axis=1)
        else:
            num = np.sum(ds * dy, axis=1)
            den = np.sum(dy * dy, axis=1)

        # Terms with denominators equal to zero are set to 1e-4
        self.tau = 1e-4 * np.ones_like(num)
        self.tau[den != 0] = num[den != 0] / den[den != 0]

        # ---------------------------------------------------------------------

        self.mxH.shape = (-1, 3)
        self.mxmxH.shape = (-1, 3)
        self.spin.shape = (-1, 3)

        mxH_sq_norm = np.sum(self.mxH ** 2, axis=1)
        factor_plus = 4 + (self.tau ** 2) * mxH_sq_norm
        factor_minus = 4 - (self.tau ** 2) * mxH_sq_norm

        new_spin = factor_minus[:, np.newaxis] * self.spin - (4 * self.tau)[:, np.newaxis] * self.mxmxH
        new_spin = new_spin / factor_plus[:, np.newaxis]

        self.mxH.shape = (-1,)
        self.mxmxH.shape = (-1,)
        self.spin.shape = (-1,)

        self.spin_last[:] = self.spin[:]
        self.spin[:] = new_spin.reshape(-1,)[:]

        # ---------------------------------------------------------------------

        # self.compute_rhs(self.tau)

        clib.normalise_spin(self.spin, self._pins, self.n)

    def update_effective_field(self):

        self.field[:] = 0

        for obj in self.interactions:
            self.field += obj.compute_field(t=0, spin=self.spin)

    def minimize(self, stopping_dm=1e-2, max_count=2000):
        self.counter = 0

        self.spin_last[:] = self.spin[:]
        self.update_effective_field()
        self.mxH[:] = self.field_cross_product(self.spin, self.field)[:]
        self.mxmxH[:] = self.field_cross_product(self.spin, self.mxH)[:]
        while self.counter < max_count:

            self.run_step()

            max_dm = (self.spin - self.spin_last).reshape(-1, 3) ** 2
            max_dm = np.max(np.sum(max_dm, axis=1))
            print("#max_tau={:<8.3g} max_dm={:<10.3g} counter={}".format(
                np.max(np.abs(self.tau)),
                max_dm, self.counter))
            if max_dm < stopping_dm and self.counter > 0:
                break

            self.counter += 1

            # update field before saving data
            # self.update_effective_field()
            # self.data_saver.save()

        # clib.normalise_spin(self.spin, self._pins, self.n)

    def relax(self):
        print('Not implemented for the minimizer')
