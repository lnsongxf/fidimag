#include "clib.h"

/*
 compute the effective exchange field at site i
 
 H_i = J \sum_<i,j> S_j
 
 with Hamiltonian
 
 Hamiltonian = - J \sum_<i,j> S_i \cdot S_j
 
 Note that the pair <i,j> only run once for each pair.
 
 */
void compute_exch_field(double *spin, double *field, double J, int nx, int ny, int nz, int xperiodic, int yperiodic) {
    
	int nyz = ny * nz;
	int n1 = nx * nyz, n2 = 2 * n1;
	int i, j, k;
	int index, id;
	double fx,fy,fz;
	for (i = 0; i < nx; i++) {
        for (j = 0; j < ny; j++) {
            for (k = 0; k < nz; k++) {
                
                index = nyz * i + nz * j + k;
                
                fx=0;
                fy=0;
                fz=0;
                
                if (k > 0) {
                    id = index - 1;
                    fx += J * spin[id];
                    fy += J * spin[id + n1];
                    fz += J * spin[id + n2];
                }
                
                if (j > 0 || yperiodic) {
                    id = index - nz;
                    if (j==0) {
                        id += nyz;
                    }
                    fx += J * spin[id];
                    fy += J * spin[id + n1];
                    fz += J * spin[id + n2];
                }
                
                if (i > 0 || xperiodic) {
                    id = index - nyz;
                    if (i==0) {
                        id += n1;
                    }
                    fx += J * spin[id];
                    fy += J * spin[id + n1];
                    fz += J * spin[id + n2];
                }
                
                if (i < nx - 1 || xperiodic) {
                    id = index + nyz;
                    if (i == nx-1){
                        id -= n1;
                    }
                    fx += J * spin[id];
                    fy += J * spin[id + n1];
                    fz += J * spin[id + n2];
                }
                
                if (j < ny - 1 || yperiodic) {
                    id = index + nz;
                    if (j == ny-1){
                        id -= nyz;
                    }
                    fx += J * spin[id];
                    fy += J * spin[id + n1];
                    fz += J * spin[id + n2];
                }
                
                if (k < nz - 1) {
                    id = index + 1;
                    fx += J * spin[id];
                    fy += J * spin[id + n1];
                    fz += J * spin[id + n2];
                }
                
                field[index] = fx;
                field[index + n1] = fy;
                field[index + n2] = fz;
                
            }
        }
	}
}

double compute_exch_energy(double *spin, double J, int nx, int ny, int nz, int xperiodic, int yperiodic) {
    
	int nyz = ny * nz;
	int n1 = nx * nyz, n2 = 2 * n1;
	int i, j, k;
	int index, id;
	double Sx, Sy, Sz;
	double energy = 0;
    
	for (i = 0; i < nx; i++) {
        for (j = 0; j < ny; j++) {
            for (k = 0; k < nz; k++) {
                index = nyz * i + nz * j + k;
                Sx = spin[index];
                Sy = spin[index + n1];
                Sz = spin[index + n2];
                
                if (i < nx - 1 || xperiodic) {
                    id = index + nyz;
                    if (i == nx-1){
                        id -= n1;
                    }
                    energy += J * Sx * spin[id];
                    energy += J * Sy * spin[id + n1];
                    energy += J * Sz * spin[id + n2];
                }
                
                if (j < ny - 1 || yperiodic) {
                    id = index + nz;
                    if (j == ny-1){
                        id -= nyz;
                    }
                    energy += J * Sx * spin[id];
                    energy += J * Sy * spin[id + n1];
                    energy += J * Sz * spin[id + n2];
                }
                
                if (k < nz - 1) {
                    id = index + 1;
                    energy += J * Sx * spin[id];
                    energy += J * Sy * spin[id + n1];
                    energy += J * Sz * spin[id + n2];
                }
                
            }
        }
	}
    
	energy = -energy;
    
	return energy;
    
}
