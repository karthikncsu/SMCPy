'''
Notices:
Copyright 2018 United States Government as represented by the Administrator of
the National Aeronautics and Space Administration. No copyright is claimed in
the United States under Title 17, U.S. Code. All Other Rights Reserved.

Disclaimers
No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF
ANY KIND, EITHER EXPRessED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
IMPLIED WARRANTIES OF MERCHANTABILITY, FITNess FOR A PARTICULAR PURPOSE, OR
FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL BE ERROR
FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED, WILL CONFORM TO THE
SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, CONSTITUTE AN
ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS,
RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS
RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY
DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE, IF
PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."

Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST THE
UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY
PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS IN ANY
LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH USE,
INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM, RECIPIENT'S
USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD HARMLess THE
UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY
PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.  RECIPIENT'S SOLE REMEDY FOR
ANY SUCH MATTER SHALL BE THE IMMEDIATE, UNILATERAL TERMINATION OF THIS
AGREEMENT.
'''

import numpy as np

from .smc.initializer import Initializer
from .smc.updater import Updater
from .smc.mutator import Mutator

class SMCSampler:

    def __init__(self, mcmc_kernel):
        self._mcmc_kernel = mcmc_kernel

    def sample(self, num_particles, num_mcmc_samples, phi_sequence,
               ess_threshold):

        initializer = Initializer(self._mcmc_kernel, phi_sequence[1])
        updater = Updater(ess_threshold)
        mutator = Mutator(self._mcmc_kernel)

        particles = initializer.init_particles_from_prior(num_particles)
        step_list = [particles]
        for i, phi in enumerate(phi_sequence[2:]):
            particles = updater.update(particles, phi - phi_sequence[i + 1])
            particles = mutator.mutate(particles, phi, num_mcmc_samples)
            step_list.append(particles)

        return step_list

    @classmethod
    def estimate_marginal_log_likelihood(clss_, step_list, phi_sequence):
        num_particles = step_list[0].num_particles

        delta_phi = np.diff(phi_sequence)[1:].reshape(1, -1)
        log_weights = np.zeros((num_particles, delta_phi.shape[1]))
        log_likes = np.zeros((num_particles, delta_phi.shape[1]))

        for i, step in enumerate(step_list[:-1]):
            log_weights[:, i] = step.log_weights.flatten()
            log_likes[:, i] = step.log_likes.flatten()

        marg_log_like = log_weights + log_likes * delta_phi
        marg_log_like = clss_._logsum(marg_log_like)

        return np.sum(marg_log_like)

    @staticmethod
    def _logsum(Z):
        Z = -np.sort(-Z, axis=0) # descending
        Z0 = Z[0, :]
        Z_shifted = Z[1:, :] - Z0
        return Z0 + np.log(1 + np.sum(np.exp(Z_shifted), axis=0))
