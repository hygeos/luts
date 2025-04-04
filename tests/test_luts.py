#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import tempfile
import warnings

import numpy as np
import pytest

from luts import LUT, MLUT, Idx, merge, read_mlut, read_mlut_hdf


def create_mlut():
    np.random.seed(0)
    m = MLUT()
    m.add_axis('a', np.linspace(100, 150, 5))
    m.add_axis('b', np.linspace(5, 8, 6))
    m.add_axis('c', np.linspace(0, 1, 7))
    m.add_dataset('data1', np.arange(5*6, dtype='float').reshape(5,6), ['a', 'b'], attrs={'a1': 12})
    m.add_dataset('data2', np.random.randn(5, 6, 7), ['a', 'b', 'c'])
    m.add_dataset('data3', np.random.randn(10, 12))
    m.set_attr('x', 12)   # set MLUT attributes
    m.set_attrs({'y':15, 'z':8})

    return m

def create_lut():
    z = np.linspace(0, 120., 80)
    P0 = np.linspace(980, 1030, 6)
    Pdata = P0.reshape(1,-1)*np.exp(-z.reshape(-1,1)/8) # dimensions (z, P0)
    return LUT(Pdata, axes=[z, P0], names=['z', 'P0'], desc='Pdata', attrs={'unit': 'HPa'})

def test_scalar():
    '''
    Add a scalar dataset (0 dimensions) and make some operations with it
    '''
    m = create_mlut()
    m.add_dataset('scalar', np.array(1.), attrs={'desc': 'scalar value'})
    m['scalar'].print_info()
    (m['scalar']+m['scalar']).apply(np.sqrt).print_info()

    m.describe()
    for fmt in ['hdf4', 'netcdf4']:
        with tempfile.NamedTemporaryFile() as f:
            m.save(f.name, overwrite=True, verbose=True, fmt=fmt)
            assert m.equal(read_mlut(f.name, fmt=fmt), show_diff=True)


def test_mlut_index1():
    m = create_mlut()
    with pytest.raises(Exception):
        m['data4']

def test_mlut_index2():
    m = create_mlut()
    m['data1']


@pytest.mark.parametrize('fn,result', [
    (lambda x, y: x+y, 9.),
    (lambda x, y: x-y, 5.),
    (lambda x, y: y-x, -5.),
    (lambda x, y: x*y, 14.),
    (lambda x, y: x/y, 3.5),
])
def test_lut_oper1(fn, result):
    '''
    test operations on LUTs
    '''
    m0 = create_mlut()
    m0.set_attr('z', 5)
    m1 = create_mlut()
    m1['data1'].data[:] = 2

    # check that same result is obtained through LUT and array operations
    for i in ['data1', 'data2', 'data3']:
        res = fn(m0[i], m1[i])
        assert np.allclose(res.data, fn(m0[i].data, m1[i].data))
        assert 'x' not in res.attrs

        if i == 'data1':
            assert res[1,1] == result


def test_lut_oper2():
    '''
    LUT operation between LUTs with incompatible shapes
    '''
    L0 = LUT(np.arange(5))
    L1 = LUT(np.arange(10))
    with pytest.raises(ValueError):
        L0 + L1


@pytest.mark.parametrize('op,res', [
    (lambda x: x+2, 9.),
    (lambda x: 2+x, 9.),
    (lambda x: x-2, 5.),
    (lambda x: 2-x, -5.),
    (lambda x: x*2, 14.),
    (lambda x: 2*x, 14.),
    (lambda x: x/2, 3.5),
    (lambda x: 2./(x+1), 0.25),
])
def test_lut_oper3(op, res):
    '''
    Scalar operations between LUTs
    '''
    m0 = create_mlut()

    # operate on the LUT
    assert op(m0['data1'])[1, 1] == res

    # operate on the array
    assert op(m0['data1'][1, 1]) == res


def test_broadcasting1():
    # "broadcasting" operations between LUTs
    l = create_lut()
    l.names[0] = 'zz'
    p = create_lut()
    assert (p+l).names == ['z', 'zz', 'P0']
    assert (p+l)[2, 3, 4] == p[2, 4] + l[3, 4]

def test_broadcasting2():
    l = create_lut()
    z = l.sub()[:, 0]
    p = l.sub()[0, :]
    (z + p).print_info()
    assert (z+p)[4, 5] == z[4] + p[5]

def test_sub():
    l = create_lut()

    assert l.sub()[1, :] == l.sub({'z': 1})
    assert l.sub()[1, :] == l.sub({0: 1})
    assert l.sub()[1.4, :] == l.sub({'z': 1.4})
    assert l.sub()[Idx(50), :] == l.sub({'z':Idx(50)})
    l.sub({'z': 1.4, 'P0': 4}).print_info()

def test_getitem():
    # test interpolation
    l = create_lut()
    l[2.5, 1.5]
    l[2.5, Idx(1000)]
    l[2.5, np.ones((4, 4), dtype='float')*1.5]
    l[Idx(100.), Idx(np.ones((4, 4))*1000.)]


def test_sub2():
    # test more complex subsetting
    # using arrays, etc
    l = create_lut()

    l.sub({'z': np.arange(3)})

    l.sub({'z': l.axis('z') < 50})

    l.sub({'z': Idx(lambda x: x<50.)}).describe()

    l.sub({'P0': Idx(1002)}).describe()

    l.sub({'P0': slice(None,None,2)}).describe()


def test_sub3():
    # subsetting MLUTs
    m = create_mlut()
    mm = m.sub({'b': Idx(lambda x: x<7)}).describe()
    assert (mm.axis('b') < 7).all()

def test_sub4():
    LUT(np.eye(4)).sub({0: np.arange(2, dtype='int')}).describe()

def test_sub5():
    LUT(np.eye(4)).sub({1: slice(None,None,2)}).describe()

def test_sub6():
    LUT(np.eye(4)).sub()[:,:].describe()

def test_broadcasting3():
    l1 = LUT(np.eye(3), axes=[None, None], names=['a', 'b'])
    l2 = LUT(np.eye(3), axes=[None, None], names=['b', 'a'])
    with pytest.raises(ValueError):
        l1+l2

def test_dimensions():
    l2 = LUT(np.zeros((2, 3, 4, 5)),
             axes=[np.arange(2),np.arange(3),np.arange(4),np.arange(5)],
             names=['2', '3', '4', '5'])
    i1 = np.zeros(10, dtype='int')
    i2 = np.eye(10, dtype='int')
    assert l2[i1, 0, :,:].shape == (10,4,5)
    assert l2[i2, 0, :,:].shape == (10,10,4,5)
    assert l2[:,i2,0,:].shape == (2,10,10,5)
    assert l2[:,i2,0,i2].shape == (2,10,10)
    assert l2[:,i2,0,:].shape == (2,10,10,5)

def test_reduce():
    l = create_lut()
    l.print_info()
    l.reduce(np.sum, 'z')
    l.reduce(np.sum, 'P0')
    l.reduce(np.sum, 0)
    l.reduce(np.sum, 1)


def test_reduce_2():
    # test reduce using grouping
    l = create_lut()
    P0 = l.axis('P0')
    l.reduce(np.sum, 'P0', grouping=(P0<1000))
    l.reduce(np.sum, 'P0', grouping=(P0<1000))


def test_indexing():
    m = create_mlut()
    for i, d in enumerate(m.datasets()):
        if m[d].ndim == 2:
            assert np.allclose(m[d][:,:], m[i][:,:])
        elif m[d].ndim == 3:
            assert np.allclose(m[d][:,:,:], m[i][:,:,:])


@pytest.mark.parametrize('t0', ['i', 'f', 'imi', 'imf', ':'])
@pytest.mark.parametrize('t1', ['i', 'f', 'imi', 'imf', ':'])
@pytest.mark.parametrize('t2', ['i', 'f', 'imi', 'imf', ':'])
@pytest.mark.parametrize('t3', ['i', 'f', 'imi', 'imf', ':'])
def test_indexing1(t0, t1, t2, t3):
    '''
    check many indexing methods
    '''
    inputs = {
            'i': 0,
            'f': 0.25,
            'imf': np.random.random((2, 3)),
            'imi': np.zeros((2, 3), dtype='int'),
            ':': slice(None)
            }
    i0 = inputs[t0]
    i1 = inputs[t1]
    i2 = inputs[t2]
    i3 = inputs[t3]
    print('indices are "{},{},{},{}"'.format(i0, i1, i2, i3))

    D = np.random.randn(8,9,10,11)
    L = LUT(D)
    L[i0, i1, i2, i3].shape


def test_axis():
    m = create_mlut()
    assert np.all(m.axis('a') == m.axes['a'])
    assert np.all(m.axis('a', aslut=True)[:] == m.axes['a'])

    l = create_lut()
    assert np.all(l.axis('z') == l.axes[0])
    assert np.all(l.axis(0) == l.axes[0])
    assert np.all(l.axis('z', aslut=True)[:] == l.axes[0])
    assert np.all(l.axis(0, aslut=True)[:] == l.axes[0])

def test_dropaxis():
    m = MLUT()
    m.add_axis('a', [1])
    m.add_axis('b', np.linspace(5, 8, 6))
    m.add_axis('c', [12])
    m.add_dataset('data1', np.random.randn(1, 6, 1), ['a', 'b', 'c'])
    m.add_dataset('data2', np.random.randn(1, 6), ['c', 'b'])
    m.add_dataset('data3', np.random.randn(1, 1), ['a', 'c'])
    m.attrs = {'un':1, 'deux':2}

    assert m.dropaxis('a')['data1'].shape == (6, 1)
    assert m.dropaxis('a', 'c')['data3'].data == m['data3'][0,0]
    assert m.dropaxis('a', 'c')['data3'].shape == ()
    assert m.dropaxis('a', 'c').attrs == m.attrs

def test_merge():
    mluts = []
    for p1 in np.arange(5):
        for p2 in np.arange(3):
            m = create_mlut()
            m.set_attr('p1', p1)
            m.set_attr('p2', p2)
            mluts.append(m)
    m = merge(mluts, ['p1', 'p2'])

    assert len(m.datasets()) == 3
    assert m[0].shape == (5, 3, 5, 6)
    assert 'x' in m.attrs

    for l in m:
        assert not np.isnan(l.data).any()


def test_equality():
    m0 = create_mlut()
    m1 = create_mlut()

    assert m0 == m1
    assert m0 != 2

def test_equality2():
    l0 = create_lut()
    l1 = create_lut()

    assert l0 == l1
    assert l0 != 2

    l1.attrs['another'] = 'attribute'
    assert l0 != l1

def test_modify_axis():
    l = create_lut()
    l.axis('z')[2] = 0
    assert l.axis('z')[0] == 0

    # same for mlut
    m = create_mlut()
    m[0].axis(1)[0] = -10
    assert m[0].axis(1)[0] == -10

def test_idx1():
    with pytest.raises(ValueError):
        Idx(2.5).index(np.array([2.]))

def test_idx2():
    with pytest.raises(ValueError):
        Idx(np.eye(2)).index(np.array([2.]))

def test_idx3():
    Idx(2.5).index(np.array([2.5]))

def test_idx4():
    assert Idx(2.5).index(np.arange(10)*2) == 1.25

def test_idx5():
    np.allclose(Idx(np.eye(2)).index(np.linspace(0, 5, 5)), 0.8*np.eye(2))

def test_idx6():
    with pytest.raises(ValueError):
        Idx(np.eye(2)).index(np.linspace(1, 5, 5))

def test_idx7():
    r = Idx(np.eye(2), fill_value=np.nan).index(np.linspace(2, 5, 5))
    assert np.isnan(r).all()

def test_idx8():
    idx = Idx(lambda x: x<5)
    assert (idx.index(np.arange(10)+100) < 10).all()
    assert (idx.apply(np.arange(10)+100) >= 100).all()

def test_idx_oob_1():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert Idx(-1, fill_value='extrema').index(np.arange(10)) == 0.
        assert Idx(100, fill_value='extrema').index(np.arange(10)) == 9.

    with pytest.warns() as record:
        assert Idx(-1, fill_value='extrema,warn').index(np.arange(10)) == 0.
        assert Idx(100, fill_value='extrema,warn').index(np.arange(10)) == 9.
        assert len(record) == 2



def test_convert():
    m = MLUT()
    m.add_axis('a', np.linspace(100, 150, 5))
    m.add_axis('b', np.linspace(5, 8, 6))
    m.add_dataset('data1', np.arange(5*6, dtype='float').reshape(5,6), ['a', 'b'])
    m.set_attr('x', 12)   # set MLUT attributes
    m.set_attrs({'y':15, 'z':8})

    assert m.equal(m[0].to_mlut(), attributes=False)

def test_oper_lut1():
    l = create_lut()
    assert (l+2).desc == l.desc

def test_oper_lut2():
    l = create_lut()
    m = create_lut()
    assert (l+m).desc == l.desc
    assert np.allclose((l+m).data, (l.data)+(m.data))
    m.desc = 'another'
    assert (l+m).desc != l.desc

def test_lut_apply():
    l = create_lut()
    m = l.apply(np.sqrt)
    assert m.desc == l.desc
    m = l.apply(np.sqrt, 'test')
    assert m.desc == 'test'
    assert np.allclose(m.data, np.sqrt(l.data))


@pytest.mark.parametrize('filename', ['mlut.hdf', 'mlut.nc'])
def test_write_read_mlut(filename):

    # write a mlut, read it again, should be equal
    with tempfile.TemporaryDirectory() as tmpdir:
        m0 = create_mlut()
        filename = os.path.join(tmpdir,filename)
        m0.save(filename)
        m1 = read_mlut(filename)

        assert m0.equal(m1, show_diff=True)



def test_write_read_mlut2():
    # partial read of mlut
    m0 = create_mlut()
    for d in m0.datasets():
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'mlut.hdf')
            m0.save(filename)
            m1 = read_mlut_hdf(filename, datasets=[d])

            assert m0[d] == m1[0]


def test_names_axes_without_values():
    '''
    datasets with named axes but without values
    '''
    m = MLUT()
    m.add_axis('b', np.linspace(100, 200, 10))
    m.add_dataset('data', np.zeros((5, 10, 20)), axnames=['a', 'b', 'c'])
    m['data']
    m['data'][0,0,0]
    m['data'][:,:,:]

def test_add_lut():
    '''
    test add a LUT to a MLUT
    '''
    l = create_lut()
    m = create_mlut()
    m.add_lut(l)
    assert len(m.axes) == 5
    assert m[l.desc].equal(l)


def test_swapaxes():
    l = create_mlut()['data2']
    l.print_info()
    l.swapaxes('b', 'c')

    a = l
    a = a.swapaxes('a', 'c')
    a = a.swapaxes('a', 'c')
    assert a == l

    a = l
    a = a.swapaxes('b', 'c')
    a = a.swapaxes('a', 'c')
    a = a.swapaxes('a', 'c')
    a = a.swapaxes('b', 'c')
    assert a == l

    assert l.swapaxes(0,2).sub()[:,:,0] == l.sub()[0,:,:].swapaxes(0,1)

def test_lut_string():
    LUT(np.array(['abc', 'def', 'hij']))[2]

def test_rm_lut():
    m = create_mlut()
    m.rm_lut('data1')

def test_rename_lut():
    l = create_lut()
    l.describe()
    l.rename_axis('z', 'zz')
    l.describe()

def test_rename_mlut():
    m = create_mlut()
    m.rename_axis('a', 'aa')
    m.rename_axis('b', 'bb').rename_axis('c', 'cc')

def test_plot_polar():
    m = create_mlut()
    m['data1'].plot_polar()
