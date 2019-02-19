import itertools
import collections
from copy import copy
from types import SimpleNamespace
import tinyarray as ta
import kwant
import numpy as np
import holoviews as hv

if tuple(int(i) for i in np.__version__.split('.')[:3]) <= (1, 8, 0):
    raise RuntimeError("numpy >= (1, 8, 0) is required")

__all__ = ['haldaneModel', 'spectrum', 'hamiltonian_array', 'h_k', 'pauli']


def haldaneModel(w = 20, boundary = 'zigzag', pVecs = [(1.0,0.0),(1/2,np.sqrt(3)/2)] , bAtoms = [(0.0,0.0),(0.0,1/np.sqrt(3))]):
    """Function which creates graphene lattice with nearest and next nearest
       neighbor hopping based on Haldane model.

    Parameters:
    -----------
    w :        width of lattice, for use with boundary ribbons in finite systems.

    boundary : creates a boundary based on 'zigzag' or 'armchair' bounary 
               conditions. If a string other than 'zigzag' or 'armchair' 
               is given the system is assumed to be infinite.

    pvecs :    primitive vectors of the lattice.
               2d array-like of floats. The primitive vectors of the Bravais lattice
               If None selected pVecs = [(1.0,0.0),(1/2,np.sqrt(3)/2)]

    bAtoms :   basis atoms of the lattice.
               2d array-like of floats. The coordinates of the basis sites inside the unit cell
               If None selected bAtoms = [(0.0,0.0),(0.0,1/np.sqrt(3))]

    Returns:
    --------
    kwant.Builder object The un-finalized (in)finite system.

    """

    for iVec in range(0,len(pVecs)):
        if len(pVecs[iVec]) != 2:
            raise ValueError("haldane model must be 2D")

    for iAtomCoord in range(0,len(bAtoms)):
        if len(bAtoms[iAtomCoord]) != 2:
            raise ValueError("haldane model must be 2D")

    def ribbonShapeZigzag(pos):
        return (-0.5 / np.sqrt(3) - 0.1 <= pos[1] < np.sqrt(3) * w / 2 + 0.01)

    def ribbonShapeArmchair(pos):
        return (-1 <= pos[0] < w)

    def onsite(site, p):
        if site.family == a:
            return p.m
        else:
            return -p.m

    ### nearest neighbor hoppings ###
    def nnHopping(site1, site2, p):
        return p.t

    ### next nearest neighbor hoppings ###
    def nnnHopping(site1, site2, p):
        return 1j * p.t_2

    # The first argument to the general function is the list of primitive vectors of the lattice
    # The second one is the coordinates of basis atoms. The honeycomb lattice has two basis atoms
    lat = kwant.lattice.general(pVecs,bAtoms)
    a, b = lat.sublattices

    ### Create next nearest neighbor hoppings ###
    nnnHoppings_a = (((-1, 0), a, a), ((0, 1), a, a), ((1, -1), a, a))
    nnnHoppings_b = (((1, 0), b, b), ((0, -1), b, b), ((-1, 1), b, b))

    if boundary == 'zigzag':
        syst = kwant.Builder(kwant.TranslationalSymmetry((1, 0)))
        syst[lat.shape(ribbonShapeZigzag, (0, 0))] = onsite

    elif boundary == 'armchair':
        syst = kwant.Builder(kwant.TranslationalSymmetry((0, np.sqrt(3))))
        syst[lat.shape(ribbonShapeArmchair, (0, 0))] = onsite

    else:
        syst = kwant.Builder(kwant.TranslationalSymmetry(*lat.prim_vecs)) 
        syst[lat.shape(lambda pos: True, (0, 0))] = onsite
    
    syst[lat.neighbors()] = nnHopping
    syst[[kwant.builder.HoppingKind(*hopping) for hopping in nnnHoppings_a]] = nnnHopping
    syst[[kwant.builder.HoppingKind(*hopping) for hopping in nnnHoppings_b]] = nnnHopping

    return syst


def spectrum(syst, p=None, k_x=None, k_y=None, k_z=None, title=None, xdim=None,
             ydim=None, zdim=None, xticks=None, yticks=None, zticks=None,
             xlims=None, ylims=None, zlims=None, num_bands=None, res=101, return_energies=False):
    """Function that plots system spectrum for varying parameters or momenta.

    Parameters:
    -----------
    syst : kwant.Builder object
        The un-finalized (in)finite system.
    p : SimpleNamespace object
        A container used to store Hamiltonian parameters. The parameters that
        are sequences are used as plot axes.
    k_x, k_y, k_z : floats or sequences of floats
        Real space momenta at which the Hamiltonian has to be evaluated.
        If the system dimensionality is low, extra momenta are ignored.
    title : function or str
        Function that takes p as argument and generates a string. If a string
        it's used as static title.
    xdim, ydim, zdim : holoviews.Dimension or string
        The labels of the axes. Default to best guess, and extra ones
        are ignored.
    xticks, yticks zticks : list
        Lists of axes xticks, extra ones are ignored.
    xlims, ylims, zlims : tuple
        Upper and lower plot limit of the axes. If None the upper and lower
        limits of the ticks are used. Extra ones are ignored.
    num_bands : int
        Number of bands that should be plotted, only works for 2D plots. If
        None all bands are plotted.
    return_energies : bool
        If True the function only returns the energies in an array.

    Returns:
    --------
    plot : holoviews.Path object
        Plot of varying parameter vs. spectrum.
    """
    pi_ticks = [(-np.pi, r'$-\pi$'), (0, '$0$'), (np.pi, r'$\pi$')]
    if p is None:
        p = SimpleNamespace()
    dimensionality = syst.symmetry.num_directions
    k = [k_x, k_y, k_z]
    k = [(np.linspace(-np.pi, np.pi, res) if i is None else i)
         for i in k]
    k = [(i if j < dimensionality else 0) for (j, i) in enumerate(k)]
    k_x, k_y, k_z = k

    hamiltonians, variables = hamiltonian_array(syst, p, k_x, k_y, k_z, True)
    # Don't waste effort calculating eigenvalues if we aren't going to plot
    # anything.
    if len(variables) in (1, 2):
        energies = np.linalg.eigvalsh(hamiltonians)

    if len(variables) == 0:
        raise ValueError("A 0D plot requested")

    if return_energies:
        return energies

    elif len(variables) == 1:
        # 1D plot.
        if xdim is None:
            if variables[0][0] in 'k_x k_y k_z'.split():
                xdim = r'${}$'.format(variables[0][0])
            else:
                xdim = variables[0][0]
        if ydim is None:
            ydim = r'$E$'

        plot = hv.Path((variables[0][1], energies), kdims=[xdim, ydim])

        ticks = {}
        if isinstance(xticks, collections.Iterable):
            ticks['xticks'] = list(xticks)
        elif xticks is None:
            pass
        else:
            ticks['xticks'] = xticks

        if isinstance(yticks, collections.Iterable):
            ticks['yticks'] = list(yticks)
        elif isinstance(yticks, int):
            ticks['yticks'] = yticks

        xlims = slice(*xlims) if xlims is not None else slice(None)
        ylims = slice(*ylims) if ylims is not None else slice(None)

        if callable(title):
            plot = plot.relabel(title(p))
        elif isinstance(title, str):
            plot = plot.relabel(title)

        return plot[xlims, ylims](plot={'Path': ticks})

    elif len(variables) == 2:
        # 2D plot.
        style = {}
        if xticks is None and variables[0][0] in 'k_x k_y k_z'.split():
            style['xticks'] = pi_ticks
        elif xticks is not None:
            style['xticks'] = list(xticks)
        if yticks is None and variables[1][0] in 'k_x k_y k_z'.split():
            style['yticks'] = pi_ticks
        elif yticks is not None:
            style['yticks'] = list(yticks)

        if xdim is None:
            if variables[0][0] in 'k_x k_y k_z'.split():
                xdim = r'${}$'.format(variables[0][0])
            else:
                xdim = variables[0][0]
        if ydim is None:
            if variables[1][0] in 'k_x k_y k_z'.split():
                ydim = r'${}$'.format(variables[1][0])
            else:
                ydim = variables[1][0]
        if zdim is None:
            zdim = r'$E$'

        if zticks is not None:
            style['zticks'] = zticks

        if xlims is None:
            xlims = np.round([min(variables[0][1]), max(variables[0][1])], 2)
        if ylims is None:
            ylims = np.round([min(variables[1][1]), max(variables[1][1])], 2)
        if zlims is None:
            zlims = (None, None)

        kwargs = {'extents': (xlims[0], ylims[0], zlims[0],
                              xlims[1], ylims[1], zlims[1]),
                  'kdims': [xdim, ydim],
                  'vdims': [zdim]}

        if num_bands is None:
            plot = hv.Overlay([hv.Surface(energies[:, :, i], **kwargs)(plot=style) 
                               for i in range(energies.shape[-1])])
        else:
            mid = energies.shape[-1] // 2
            num_bands //= 2
            plot = hv.Overlay([hv.Surface(energies[:, :, i], **kwargs)(plot=style) 
                               for i in range(mid - num_bands, mid + num_bands)])

        if callable(title):
            plot = plot.relabel(title(p))
        elif isinstance(title, str):
            plot = plot.relabel(title)

        return plot(plot={'Overlay': {'fig_size': 200}})

    else:
        raise ValueError("Cannot make 4D plots yet.")


def h_k(syst, p, momentum):
    """Function that returns the Hamiltonian of a kwant 1D system as a momentum.
    """
    return hamiltonian_array(syst, p, momentum)[0]


def hamiltonian_array(syst, p=None, k_x=0, k_y=0, k_z=0, return_grid=False):
    """Evaluate the Hamiltonian of a system over a grid of parameters.

    Parameters:
    -----------
    syst : kwant.Builder object
        The un-finalized kwant system whose Hamiltonian is calculated.
    p : SimpleNamespace object
        A container of Hamiltonian parameters. The parameters that are
        sequences are used to loop over.
    k_x, k_y, k_z : floats or sequences of floats
        Momenta at which the Hamiltonian has to be evaluated.  If the system
        only has 1 translation symmetry, only `k_x` is used, and interpreted as
        lattice momentum. Otherwise the momenta are in reciprocal space.
    return_grid : bool
        Whether to also return the names of the variables used for expansion,
        and their values.

    Returns:
    --------
    hamiltonians : numpy.ndarray
        An array with the Hamiltonians. The first n-2 dimensions correspond to
        the expanded variables.
    parameters : list of tuples
        Names and ranges of values that were used in evaluation of the
        Hamiltonians.

    Examples:
    ---------
    >>> hamiltonian_array(syst, SimpleNamespace(t=1, mu=np.linspace(-2, 2)),
    ...                   k_x=np.linspace(-np.pi, np.pi))
    >>> hamiltonian_array(sys_2d, p, np.linspace(-np.pi, np.pi),
    ...                   np.linspace(-np.pi, np.pi))

    """
    if p is None:
        p = SimpleNamespace()
    try:
        space_dimensionality = syst.symmetry.periods.shape[-1]
    except AttributeError:
        space_dimensionality = 0
    dimensionality = syst.symmetry.num_directions
    pars = copy(p)
    if dimensionality == 0:
        syst = syst.finalized()
        def momentum_to_lattice(k):
            return []
    else:
        if len(syst.symmetry.periods) == 1:
            def momentum_to_lattice(k):
                if any(k[dimensionality:]):
                    raise ValueError("Dispersion is 1D, but more momenta are provided.")
                return [k[0]]
        else:
            B = np.array(syst.symmetry.periods).T
            A = B @ np.linalg.inv(B.T @ B)

            def momentum_to_lattice(k):
                k, residuals = np.linalg.lstsq(A, k[:space_dimensionality])[:2]
                if np.any(abs(residuals) > 1e-7):
                    raise RuntimeError("Requested momentum doesn't correspond"
                                       " to any lattice momentum.")
                return list(k)
        syst = kwant.wraparound.wraparound(syst).finalized()

    changing = dict()
    for key, value in pars.__dict__.items():
        if isinstance(value, collections.Iterable):
            changing[key] = value

    for key, value in [('k_x', k_x), ('k_y', k_y), ('k_z', k_z)]:
        if key in changing:
            raise RuntimeError('One of the system parameters is {}, '
                               'which is reserved for momentum. '
                               'Please rename it.'.format(key))
        if isinstance(value, collections.Iterable):
            changing[key] = value

    if not changing:
        hamiltonians = syst.hamiltonian_submatrix([pars] +
                                                  momentum_to_lattice([k_x, k_y, k_z]),
                                                  sparse=False)[None, ...]
        if return_grid:
            return hamiltonians, []
        else:
            return hamiltonians

    def hamiltonian(**values):
        pars.__dict__.update(values)
        k = [values.get('k_x', k_x), values.get('k_y', k_y),
             values.get('k_z', k_z)]
        k = momentum_to_lattice(k)
        return syst.hamiltonian_submatrix(args=([pars] + k), sparse=False)

    names, values = zip(*sorted(changing.items()))
    hamiltonians = [hamiltonian(**dict(zip(names, value)))
                    for value in itertools.product(*values)]
    size = list(hamiltonians[0].shape)

    hamiltonians = np.array(hamiltonians).reshape([len(value)
                                                   for value in values] + size)

    if return_grid:
        return hamiltonians, list(zip(names, values))
    else:
        return hamiltonians
