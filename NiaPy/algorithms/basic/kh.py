# encoding=utf8
# pylint: disable=mixed-indentation, trailing-whitespace, multiple-statements, attribute-defined-outside-init, logging-not-lazy, arguments-differ, line-too-long, redefined-builtin, singleton-comparison, no-self-use, bad-continuation
import logging
from scipy.spatial.distance import euclidean as ed
from numpy import apply_along_axis, argmin, argmax, sum, full, inf, asarray, mean, where, sqrt
from NiaPy.util import fullArray
from NiaPy.algorithms.algorithm import Algorithm

logging.basicConfig()
logger = logging.getLogger('NiaPy.algorithms.basic')
logger.setLevel('INFO')

__all__ = ['KrillHerdV1', 'KrillHerdV2', 'KrillHerdV3', 'KrillHerdV4', 'KrillHerdV11']

class KrillHerd(Algorithm):
	r"""Implementation of krill herd algorithm.

	Algorithm:
		Krill Herd Algorithm

	Date:
		2018

	Authors:
		Klemen Berkovič

	License:
		MIT

	Reference URL:
		http://www.sciencedirect.com/science/article/pii/S1007570412002171

	Reference paper:
		Amir Hossein Gandomi, Amir Hossein Alavi, Krill herd: A new bio-inspired optimization algorithm, Communications in Nonlinear Science and Numerical Simulation, Volume 17, Issue 12, 2012, Pages 4831-4845, ISSN 1007-5704, https://doi.org/10.1016/j.cnsns.2012.05.010.

	Attributes:
		Name (List[str]): List of strings representing algorithm names..
		NP (int): Number of krill herds in population.
		N_max (float): Maximum induced speed.
		V_f (float): Foraging speed.
		D_max (float): Maximum diffusion speed.
		C_t (float): Constant :math:`\in [0, 2]`
		W_n (Union[int, float, numpy.ndarray]): Interta weights of the motion induced from neighbors :math:`\in [0, 1]`.
		W_f (Union[int, float, numpy.ndarray]): Interta weights of the motion induced from foraging :math`\in [0, 1]`.
		d_s (float): Maximum euclidean distance for neighbors.
		nn (int): Maximum neighbors for neighbors effect.
		Cr (float): Crossover probability.
		Mu (float): Mutation probability.
		epsilon (float): Small numbers for division.

	See Also:
		* :class:`NiaPy.algorithms.algorithm.Algorithm`
	"""
	Name = ['KrillHerd', 'KH']

	@staticmethod
	def typeParameters():
		r"""Get dictionary with functions for checking values of parameters.

		Returns:
			Dict[str, Callable]:
				* N_max (Callable[[Union[int, float]], bool]): TODO
				* V_f (Callable[[Union[int, float]], bool]): TODO
				* D_max (Callable[[Union[int, float]], bool]): TODO
				* C_t (Callable[[Union[int, float]], bool]): TODO
				* W_n (Callable[[Union[int, float]], bool]): TODO
				* W_f (Callable[[Union[int, float]], bool]): TODO
				* d_s (Callable[[Union[int, float]], boool]): TODO
				* nn (Callable[[int], bool]): TODO
				* Cr (Callable[[float], bool]): TODO
				* Mu (Callable[[float], bool]): TODO
				* epsilon (Callable[[float], bool]): TODO

		See Also:
			* :func:`NiaPy.algorithms.algorithm.Algorithm`
		"""
		d = Algorithm.typeParameters()
		d.update({
			'N_max': lambda x: isinstance(x, (int, float)) and x > 0,
			'V_f': lambda x: isinstance(x, (int, float)) and x > 0,
			'D_max': lambda x: isinstance(x, (int, float)) and x > 0,
			'C_t': lambda x: isinstance(x, (int, float)) and x > 0,
			'W_n': lambda x: isinstance(x, (int, float)) and x > 0,
			'W_f': lambda x: isinstance(x, (int, float)) and x > 0,
			'd_s': lambda x: isinstance(x, (int, float)) and x > 0,
			'nn': lambda x: isinstance(x, int) and x > 0,
			'Cr': lambda x: isinstance(x, float) and 0 <= x <= 1,
			'Mu': lambda x: isinstance(x, float) and 0 <= x <= 1,
			'epsilon': lambda x: isinstance(x, float) and 0 < x < 1
		})
		return d

	def setParameters(self, NP=50, N_max=0.01, V_f=0.02, D_max=0.002, C_t=0.93, W_n=0.42, W_f=0.38, d_s=2.63, nn=5, Cr=0.2, Mu=0.05, epsilon=1e-31, **ukwargs):
		r"""Set the arguments of an algorithm.

		Arguments:
			NP (Optional[int]): Number of krill herds in population.
			N_max (Optional[float]): Maximum induced speed.
			V_f (Optional[float]): Foraging speed.
			D_max (Optional[float]): Maximum diffusion speed.
			C_t (Optional[float]): Constant $\in [0, 2]$.
			W_n (Optional[Union[int, float, numpy.ndarray]]): Intera weights of the motion induced from neighbors :math:`\in [0, 1]`.
			W_f (Optional[Union[int, float, numpy.ndarray]]): Intera weights of the motion induced from foraging :math:`\in [0, 1]`.
			d_s (Optional[float]): Maximum euclidean distance for neighbors.
			nn (Optional[int]): Maximum neighbors for neighbors effect.
			Cr (Optional[float]): Crossover probability.
			Mu (Optional[float]): Mutation probability.
			epsilon (Optional[float]): Small numbers for division.

		See Also:
			* :func:`NiaPy.algorithms.algorithm.Algorithm.setParameters`
		"""

		Algorithm.setParameters(self, **ukwargs)
		self.NP = NP
		self.N_max, self.V_f, self.D_max, self.C_t, self.W_n, self.W_f, self.d_s, self.nn, self._Cr, self._Mu, self.epsilon = N_max, V_f, D_max, C_t, W_n, W_f, d_s, nn, Cr, Mu, epsilon
		if ukwargs: logger.info('Unused arguments: %s' % (ukwargs))

	def initWeights(self, task):
		r"""Initialize weights.

		Args:
			task (Task): Optimization task.

		Returns:
			Tuple[numpy.ndarray, numpy.ndarray]:
				1. Weights for neighborhood.
				2. Weights for foraging.
		"""
		return fullArray(self.W_n, task.D), fullArray(self.W_f, task.D)

	def sensRange(self, ki, KH):
		r"""Calculate sense range for selected individual.

		Args:
			ki (int): Selected individual.
			KH (numpy.ndarray): Krill heard population.

		Returns:
			TODO
		"""
		return sum([ed(KH[ki], KH[i]) for i in range(self.NP)]) / (self.nn * self.NP)

	def getNeighbours(self, i, ids, KH):
		r"""Get neighbours.

		Args:
			i (int): Individual looking for neighbours.
			ids (float): Maximal distance for being a neighbour.
			KH (numpy.ndarray): Current population.

		Returns:
			numpy.ndarray: Neighbours of krill heard.
		"""
		N = list()
		for j in range(self.NP):
			if j != i and ids > ed(KH[i], KH[j]): N.append(j)
		if not N: N.append(self.randint(self.NP))
		return asarray(N)

	def funX(self, x, y): return ((y - x) + self.epsilon) / (ed(y, x) + self.epsilon)

	def funK(self, x, y, b, w): return ((x - y) + self.epsilon) / ((w - b) + self.epsilon)

	def induceNeighborsMotion(self, i, n, W, KH, KH_f, ikh_b, ikh_w, task):
		Ni = self.getNeighbours(i, self.sensRange(i, KH), KH)
		Nx, Nf, f_b, f_w = KH[Ni], KH_f[Ni], KH_f[ikh_b], KH_f[ikh_w]
		alpha_l = sum(asarray([self.funK(KH_f[i], j, f_b, f_w) for j in Nf]) * asarray([self.funX(KH[i], j) for j in Nx]).T)
		alpha_t = 2 * (1 + self.rand() * task.Iters / task.nGEN)
		return self.N_max * (alpha_l + alpha_t) + W * n

	def induceForagingMotion(self, i, x, x_f, f, W, KH, KH_f, ikh_b, ikh_w, task):
		beta_f = 2 * (1 - task.Iters / task.nGEN) * self.funK(KH_f[i], x_f, KH_f[ikh_b], KH_f[ikh_w]) * self.funX(KH[i], x) if KH_f[ikh_b] < KH_f[i] else 0
		beta_b = self.funK(KH_f[i], KH_f[ikh_b], KH_f[ikh_b], KH_f[ikh_w]) * self.funX(KH[i], KH[ikh_b])
		return self.V_f * (beta_f + beta_b) + W * f

	def inducePhysicalDiffusion(self, task): return self.D_max * (1 - task.Iters / task.nGEN) * self.uniform(-1, 1, task.D)

	def deltaT(self, task): return self.C_t * sum(task.bcRange())

	def crossover(self, x, xo, Cr): return [xo[i] if self.rand() < Cr else x[i] for i in range(len(x))]

	def mutate(self, x, x_b, Mu):
		return [x[i] if self.rand() < Mu else (x_b[i] + self.rand()) for i in range(len(x))]

	def getFoodLocation(self, KH, KH_f, task):
		x_food = task.repair(asarray([sum(KH[:, i] / KH_f) for i in range(task.D)]) / sum(1 / KH_f), rnd=self.Rand)
		x_food_f = task.eval(x_food)
		return x_food, x_food_f

	def Mu(self, xf, yf, xf_best, xf_worst): return self._Mu / (self.funK(xf, yf, xf_best, xf_worst) + 1e-31)

	def Cr(self, xf, yf, xf_best, xf_worst): return self._Cr * self.funK(xf, yf, xf_best, xf_worst)

	def initPopulation(self, task):
		r"""Initialize stating population.

		Args:
			task (Task): Optimization task.

		Returns:
			Tuple[numpy.ndarray, numpy.ndarray[float], Dict[str, Any]]:
				1. Initialized population.
				2. Initialized populations function/fitness values.
				3. Additional arguments:
					* W_n (numpy.ndarray): Weights neighborhood.
					* W_f (numpy.ndarray): Weights foraging.
					* N (numpy.ndarray): TODO
					* F (numpy.ndarray): TODO

		See Also:
			* :func:`NiaPy.algorithms.algorithm.Algorithm.initPopulation`
		"""
		KH, KH_f, d = Algorithm.initPopulation(self, task)
		W_n, W_f = self.initWeights(task)
		N, F = full(self.NP, .0), full(self.NP, .0)
		d.update({'W_n': W_n, 'W_f': W_f, 'N': N, 'F': F})
		return KH, KH_f, d

	def runIteration(self, task, KH, KH_f, xb, fxb, W_n, W_f, N, F, **dparams):
		ikh_b, ikh_w = argmin(KH_f), argmax(KH_f)
		x_food, x_food_f = self.getFoodLocation(KH, KH_f, task)
		N = asarray([self.induceNeighborsMotion(i, N[i], W_n, KH, KH_f, ikh_b, ikh_w, task) for i in range(self.NP)])
		F = asarray([self.induceForagingMotion(i, x_food, x_food_f, F[i], W_f, KH, KH_f, ikh_b, ikh_w, task) for i in range(self.NP)])
		D = asarray([self.inducePhysicalDiffusion(task) for i in range(self.NP)])
		KH_n = KH + (self.deltaT(task) * (N + F + D))
		Cr = asarray([self.Cr(KH_f[i], KH_f[ikh_b], KH_f[ikh_b], KH_f[ikh_w]) for i in range(self.NP)])
		KH_n = asarray([self.crossover(KH_n[i], KH[i], Cr[i]) for i in range(self.NP)])
		Mu = asarray([self.Mu(KH_f[i], KH_f[ikh_b], KH_f[ikh_b], KH_f[ikh_w]) for i in range(self.NP)])
		KH_n = asarray([self.mutate(KH_n[i], KH[ikh_b], Mu[i]) for i in range(self.NP)])
		KH = apply_along_axis(task.repair, 1, KH_n, rnd=self.Rand)
		KH_f = apply_along_axis(task.eval, 1, KH)
		return KH, KH_f, {'W_n': W_n, 'W_f': W_f, 'N': N, 'F': F}

class KrillHerdV4(KrillHerd):
	r"""Implementation of krill herd algorithm.

	Algorithm:
		Krill Herd Algorithm

	Date:
		2018

	Authors:
		Klemen Berkovič

	License:
		MIT

	Reference URL:
		http://www.sciencedirect.com/science/article/pii/S1007570412002171

	Reference paper:
		Amir Hossein Gandomi, Amir Hossein Alavi, Krill herd: A new bio-inspired optimization algorithm, Communications in Nonlinear Science and Numerical Simulation, Volume 17, Issue 12, 2012, Pages 4831-4845, ISSN 1007-5704, https://doi.org/10.1016/j.cnsns.2012.05.010.

	Attributes:
		Name (List[str]): List of strings representing algorithm name.
	"""
	Name = ['KrillHerdV4', 'KHv4']

	@staticmethod
	def typeParameters():
		r"""Get dictionary with functions for checking values of parameters.

		Returns:
			Dict[str, Callable]:
				* TODO

		See Also:
			* :func:NiaPy.algorithms.basic.kh.KrillHerd.typeParameters`
		"""
		d = KrillHerd.typeParameters()
		del d['Cr']
		del d['Mu']
		del d['epsilon']
		return d

	def setParameters(self, NP=50, N_max=0.01, V_f=0.02, D_max=0.002, C_t=0.93, W_n=0.42, W_f=0.38, d_s=2.63, **ukwargs):
		r"""Set algorithm core parameters.

		Args:
			N_max (Optional[float]): TODO
			V_f (Optional[float]): TODO
			D_max (Optional[float]): TODO
			C_t (Optional[float]): TODO
			W_n (Optional]float]): TODO
			W_f (Optional[float]): TODO
			d_s (Optional[float]): TODO
			**ukwargs (Dict[str, Any]): Additional arguments.

      See Also:
      	* :func:NiaPy.algorithms.basic.kh.KrillHerd.KrillHerd.setParameters`
		"""
		KrillHerd.setParameters(self, NP, N_max, V_f, D_max, C_t, W_n, W_f, d_s, 4, 0.2, 0.05, 1e-31, **ukwargs)

class KrillHerdV1(KrillHerd):
	r"""Implementation of krill herd algorithm.

	Algorithm:
		Krill Herd Algorithm

	Date:
		2018

	Authors:
		Klemen Berkovič

	License:
		MIT

	Reference URL:
		http://www.sciencedirect.com/science/article/pii/S1007570412002171

	Reference paper:
		Amir Hossein Gandomi, Amir Hossein Alavi, Krill herd: A new bio-inspired optimization algorithm, Communications in Nonlinear Science and Numerical Simulation, Volume 17, Issue 12, 2012, Pages 4831-4845, ISSN 1007-5704, https://doi.org/10.1016/j.cnsns.2012.05.010.

	Attributes:
		Name (List[str]): List of strings representing algorithm name.

	See Also:
		* :func:NiaPy.algorithms.basic.kh.KrillHerd.KrillHerd`
	"""
	Name = ['KrillHerdV1', 'KHv1']

	@staticmethod
	def typeParameters():
		r"""Get dictionary with functions for checking values of parameters.

		Returns:
			Dict[str, Callable]:
				* TODO

		See Also:
			* :func:NiaPy.algorithms.basic.kh.KrillHerd.typeParameters`
		"""
		return KrillHerd.typeParameters()

	def crossover(self, x, xo, Cr):
		r"""Preform a crossover operation on individual.

		Args:
			x (numpy.ndarray): Current individual
			xo (numpy.ndarray): New individual
			Cr (float): Crossover probability

		Returns:
			numpy.ndarray: Crossoved individual
		"""
		return x

	def mutate(self, x, x_b, Mu):
		r"""Mutate individual.

		Args:
			x (numpy.ndarray): Current individual.
			x_b (numpy.ndarray): Global best individual.
			Mu (float): TODO

		Returns:
			numpy.ndarray: TODO
		"""
		return x

class KrillHerdV2(KrillHerd):
	r"""Implementation of krill herd algorithm.

	Algorithm:
		Krill Herd Algorithm

	Date:
		2018

	Authors:
		Klemen Berkovič

	License:
		MIT

	Reference URL:
		http://www.sciencedirect.com/science/article/pii/S1007570412002171

	Reference paper:
		Amir Hossein Gandomi, Amir Hossein Alavi, Krill herd: A new bio-inspired optimization algorithm, Communications in Nonlinear Science and Numerical Simulation, Volume 17, Issue 12, 2012, Pages 4831-4845, ISSN 1007-5704, https://doi.org/10.1016/j.cnsns.2012.05.010.

	Attributes:
		Name (List[str]): List of strings representing algorithm name.
	"""
	Name = ['KrillHerdV2', 'KHv2']

	@staticmethod
	def typeParameters():
		r"""Get dictionary with functions for checking values of parameters.

		Returns:
			Dict[str, Callable]:
				* TODO

		See Also:
			* :func:NiaPy.algorithms.basic.kh.KrillHerd.typeParameters`
		"""
		d = KrillHerd.typeParameters()
		del d['Mu']
		return d

	def mutate(self, x, x_b, Mu): return x

class KrillHerdV3(KrillHerd):
	r"""Implementation of krill herd algorithm.

	Algorithm:
		Krill Herd Algorithm

	Date:
		2018

	Authors:
		Klemen Berkovič

	License:
		MIT

	Reference URL:
		http://www.sciencedirect.com/science/article/pii/S1007570412002171

	Reference paper:
		Amir Hossein Gandomi, Amir Hossein Alavi, Krill herd: A new bio-inspired optimization algorithm, Communications in Nonlinear Science and Numerical Simulation, Volume 17, Issue 12, 2012, Pages 4831-4845, ISSN 1007-5704, https://doi.org/10.1016/j.cnsns.2012.05.010.
	"""
	Name = ['KrillHerdV3', 'KHv3']

	@staticmethod
	def typeParameters():
		d = KrillHerd.typeParameters()
		del d['Cr']
		return d

	def crossover(self, x, xo, Cr): return x

class KrillHerdV11(KrillHerd):
	r"""Implementation of krill herd algorithm.

	Algorithm:
		Krill Herd Algorithm

	Date:
		2018

	Authors:
		Klemen Berkovič

	License:
		MIT

	Reference URL:

	Reference paper:
	"""
	Name = ['KrillHerdV11', 'KHv11']

	def ElitistSelection(self, KH, KH_f, KHo, KHo_f):
		ipb = where(KHo_f >= KH_f)
		KHo[ipb], KHo_f[ipb] = KH[ipb], KH_f[ipb]
		return KHo, KHo_f

	def Neighbors(self, i, KH, KH_f, iw, ib, N, W_n, task):
		Rgb, RR, Kw_Kgb = KH[ib] - KH[i], KH - KH[i], KH_f[iw] - KH_f[ib]
		R = sqrt(sum(RR * RR))
		alpha_b = -2 * (1 + self.rand() * task.Iters / task.nGEN) * (KH_f[ib]) / Kw_Kgb / sqrt(sum(Rgb * Rgb)) * Rgb if KH_f[ib] < KH_f[i] else 0
		alpah_n, nn, ds = 0.0, 0, mean(R) / 5
		for n in range(self.NP):
			if R < ds and n != i:
				nn += 1
				if nn <= 4 and KH_f[i] != KH[n]: alpah_n -= (KH(n) - KH[i]) / Kw_Kgb / R[n] * RR[n]
		return W_n * N * self.N_max * (alpha_b + alpah_n)

	def Foraging(self, KH, KH_f, KHo, KHo_f, W_f, F, KH_wf, KH_bf, x_food, x_food_f, task):
		Rf, Kw_Kgb = x_food - KH, KH_wf - KH_bf
		beta_f = -2 * (1 - task.Iters / task.nGEN) * (x_food_f - KH_f) / Kw_Kgb / sqrt(sum(Rf * Rf)) * Rf if x_food_f < KH_f else 0
		Rib = KHo - KH
		beta_b = -(KHo_f - KH_f) / Kw_Kgb / sqrt(sum(Rib * Rib)) * Rib if KHo_f < KH_f else 0
		return W_f * F + self.V_f * (beta_b + beta_f)

	def Cr(self, KH_f, KHb_f, KHw_f): return 0.8 + 0.2 * (KH_f - KHb_f) / (KHw_f - KHb_f)

	def initPopulation(self, task):
		KH, KH_f, d = Algorithm.initPopulation(self, task)
		KHo, KHo_f = full([self.NP, task.D], task.optType.value * inf), full(self.NP, task.optType.value * inf)
		N, F, Dt = full(self.NP, .0), full(self.NP, .0), mean(task.bcRange()) / 2
		d.update({'KHo': KHo, 'KHo_f': KHo_f, 'N': N, 'F': F, 'Dt': Dt})
		return KH, KH_f, d

	def runIteration(self, task, KH, KH_f, xb, fxb, KHo, KHo_f, N, F, Dt, **dparams):
		w = full(task.D, 0.1 + 0.8 * (1 - task.Iters / task.nGEN))
		ib, iw = argmin(KH_f), argmax(KH_f)
		x_food, x_food_f = self.getFoodLocation(KH, KH_f, task)
		N = asarray([self.Neighbors(i, KH, KH_f, iw, ib, N[i], w, task) for i in range(self.NP)])
		F = asarray([self.Foraging(KH[i], KH_f[i], KHo[i], KHo_f[i], w, F[i], KH_f[iw], KH_f[ib], x_food, x_food_f, task) for i in range(self.NP)])
		Cr = asarray([self.Cr(KH_f[i], KH_f[ib], KH_f[iw]) for i in range(self.NP)])
		KH_n = asarray([self.crossover(KH[self.randint(self.NP)], KH[i], Cr[i]) for i in range(self.NP)])
		KH_n = KH + Dt * (F + N)
		KH = apply_along_axis(task.repair, 1, KH_n, self.Rand)
		KH_f = apply_along_axis(task.eval, 1, KH)
		KHo, KHo_f = self.ElitistSelection(KH, KH_f, KHo, KHo_f)
		return KH, KH_f, {'KHo': KHo, 'KHo_f': KHo_f, 'N': N, 'F': F, 'Dt': Dt}

# vim: tabstop=3 noexpandtab shiftwidth=3 softtabstop=3
