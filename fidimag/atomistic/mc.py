from __future__ import division
from __future__ import print_function
import os
import numpy as np
import fidimag.extensions.clib as clib
from fidimag.common.fileio import DataSaver
import fidimag.common.helper as helper
import fidimag.common.constant as const
from fidimag.common.save_vtk import SaveVTK

class MonteCarlo(object):

    def __init__(self, mesh, name='unnamed'):
        self.mesh = mesh
        self.name = name
        self.n = mesh.n
        self.n_nonzero = self.n


        self.ngs = mesh.neighbours

        self._mu_s = np.zeros(self.n, dtype=np.float)
        self.spin = np.ones(3 * self.n, dtype=np.float)
        self.spin_last = np.ones(3 * self.n, dtype=np.float)

        self.random_spin = np.zeros(3 * self.n, dtype=np.float)
        self._H = np.zeros(3 * self.n, dtype=np.float)

        self._skx_number = np.zeros(self.n, dtype=np.float)
        self.interactions = []

        self.create_tablewriter()
        self.vtk = SaveVTK(self.mesh, name=name)

        self.step = 0
        self.set_options()

    def set_options(self, J=50.0, D=0, H=None, seed=100, T=10.0):
        """
        J and D in units of k_B
        H in units of Tesla.
        """
        clib.init_random(seed)
        self.J = J
        self.D = D
        self.T = T
        self.mu_s =  1.0
        if H is not None:
            self._H[:] = helper.init_vector(H, self.mesh)
            self._H[:] = self._H[:]*const.mu_s_1/const.k_B

    def create_tablewriter(self):

        self.saver = DataSaver(self, self.name + '.txt')

        self.saver.entities['skx_num'] = {
            'unit': '<>', 
		    'get': lambda sim: sim.skyrmion_number(), 
		    'header': 'skx_num'}

        self.saver.update_entity_order()

    def set_m(self, m0=(1, 0, 0), normalise=True):
        self.spin[:] = helper.init_vector(m0, self.mesh, normalise)

        # TODO: carefully checking and requires to call set_mu first

        self.spin.shape = (-1, 3)
        for i in range(self.spin.shape[0]):
            if self._mu_s[i] == 0:
                self.spin[i, :] = 0
        self.spin.shape = (-1,)

    def get_mu_s(self):
        return self._mu_s

    def set_mu_s(self, value):
        self._mu_s[:] = helper.init_scalar(value, self.mesh)
        nonzero = 0
        for i in range(self.n):
            if self._mu_s[i] > 0.0:
                nonzero += 1

        self.n_nonzero = nonzero

    mu_s = property(get_mu_s, set_mu_s)

    def compute_average(self):
        self.spin.shape = (-1, 3)
        average = np.sum(self.spin, axis=0) / self.n_nonzero
        self.spin.shape = (-1,)
        return average

    def skyrmion_number(self):
        nx = self.mesh.nx
        ny = self.mesh.ny
        nz = self.mesh.nz
        number = clib.compute_skyrmion_number(
            self.spin, self._skx_number, nx, ny, nz, self.mesh.neighbours)
        return number


    def save_vtk(self):
        """
        Save a VTK file with the magnetisation vector field and magnetic
        moments as cell data. Magnetic moments are saved in units of
        Bohr magnetons

        NOTE: It is recommended to use a *cell to point data* filter in
        Paraview or Mayavi to plot the vector field
        """
        self.vtk.save_vtk(self.spin.reshape(-1, 3),
                          self._mu_s,
                          step=self.step)

    def save_m(self):
        if not os.path.exists('%s_npys' % self.name):
            os.makedirs('%s_npys' % self.name)
        name = '%s_npys/m_%g.npy' % (self.name, self.step)
        np.save(name, self.spin)


    def run(self, steps=1000, save_m_steps=100, save_vtk_steps=100):

        if save_m_steps is not None:
            self.save_m()

        if save_vtk_steps is not None:
            self.save_vtk()

        for step in range(1, steps + 1):
            self.step = step
            

            self.saver.save()

            if save_vtk_steps is not None:
                if step % save_vtk_steps == 0:
                    self.save_vtk()
            if save_m_steps is not None:
                if step % save_m_steps == 0:
                    self.save_m()
            
    	    print(step)



if __name__ == '__main__':
	pass