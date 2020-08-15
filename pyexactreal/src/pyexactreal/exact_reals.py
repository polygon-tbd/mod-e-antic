r"""
Finitely Generated Modules in the Real Numbers with Number Field Coefficients

The classes in this module wrap libexactreal for use in SageMath. They provide
:class:`ExactReals`, finitely generated submodules of the real modules over a
fixd real embedded number field.

EXAMPLES::

    sage: from pyexactreal import ExactReals
    sage: R = ExactReals(); R
    Real Numbers as (Rational Field)-Module

Typically, you want to fix some generators of your module. Here we take a
random number, modeling a transcendental real::

    sage: g = R.random_element(); g
    ℝ(0.303644…)

Mostly, you do not need to worry about the module structure of exact reals.
The module is automatically enlarged as needed::

    sage: g.module()
    ℚ-Module(ℝ(0.303644…))

    sage: (g * g).module()
    ℚ-Module(ℝ(0.303644…)^2)

    sage: (g + 1137).module()
    ℚ-Module(1, ℝ(0.303644…))

"""
# ********************************************************************
#  This file is part of exact-real.
#
#        Copyright (C) 2019 Julian Rüth
#
#  exact-real is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  exact-real is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with exact-real. If not, see <https://www.gnu.org/licenses/>.
# ********************************************************************

import cppyy
from sage.all import QQ, UniqueRepresentation, ZZ, RR, IntegralDomains, Morphism, Hom, SetsWithPartialMaps, NumberFieldElement, Parent, coerce
from sage.structure.element import IntegralDomainElement, coerce_binop
from sage.categories.action import Action
from sage.structure.coerce import RightModuleAction
from pyexactreal import exactreal, QQModule, ZZModule, NumberFieldModule
from pyeantic import eantic, RealEmbeddedNumberField

class ExactRealElement(IntegralDomainElement):
    r"""
    An element of :class:`ExactReals`

    This is a simple wrapper of an ``exactreal::Element`` from libexactreal to
    make it work in the Parent/Element framework of SageMath.

    EXAMPLES::

        sage: from pyexactreal import ExactReals
        sage: r = ExactReals().random_element(); r
        ℝ(0.120809…)

    TESTS::

       sage: from pyexactreal.exact_reals import ExactRealElement
       sage: isinstance(r, ExactRealElement)
       True

    """
    def __init__(self, parent, value):
        if value == 0:
            value = parent._element_factory()
        if not isinstance(value, parent._element_factory):
            raise TypeError("element must be an %s" % (parent._element_factory,))
        self._backend = value
        IntegralDomainElement.__init__(self, parent)

    def module(self):
        r"""
        Return the ``exactreal::Module`` this element lives in.

        This is the actual underlying implementation from C++ and not a
        SageMath type. You usually should not have to use this.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals()(1).module()
            ℚ-Module(1)

        TESTS:

        Since modules are internally shared pointers they are not unique::

            sage: R = ExactReals()
            sage: R(1).module() == R(1).module()
            True
            sage: R(1).module() is R(1).module()
            False
            sage: g = R.random_element()
            sage: R(g).module() == R(g).module()
            True
            sage: R(g).module() is R(g).module()
            False

        However, the objects backing these shared pointers are unique::

            sage: M,N = R(1).module(), R(1).module()
            sage: M.__smartptr__().get() is N.__smartptr__().get()
            True
            sage: M,N = R(g).module(), R(g).module()
            sage: M.__smartptr__().get() is N.__smartptr__().get()
            True

        """
        return self._backend.module()

    def _add_(self, rhs):
        r"""
        Return the sum of this element and ``rhs``.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: R.random_element() + R.random_element()
            ℝ(...) + ℝ(...)
            sage: R.random_element() + 1337
            ℝ(...) + 1337

        """
        return self.parent()(self._backend + rhs._backend)

    def _sub_(self, rhs):
        r"""
        Return the difference of this element and ``rhs``.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: R.random_element() - R.random_element()
            ℝ(...) - ℝ(...)
            sage: R.random_element() - 1337
            ℝ(...) - 1337

        """
        return self.parent()(self._backend - rhs._backend)

    def _mul_(self, rhs):
        r"""
        Return the product of this element and ``rhs``.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: R.random_element() * R.random_element() # order of factors not deterministic
            ℝ(...)*ℝ(...)

        TESTS:

        Test that integers coerce correctly::

            sage: 0 * R.random_element()
            0
            sage: R(0) * R.random_element()
            0
            sage: R.random_element() * 0
            0
            sage: R.random_element() * R(0)
            0
            sage: 1 * R.random_element()
            ℝ(...)
            sage: R(1) * R.random_element()
            ℝ(...)
            sage: R.random_element() * 1
            ℝ(...)
            sage: R.random_element() * R(1)
            ℝ(...)

        """
        return self.parent()(self._backend * rhs._backend)

    def _div_(self, rhs):
        r"""
        Return the quotient of this element and ``rhs``.

        This only works when the quotient is contained in the same module as
        the dividend.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: R.random_element() / R.random_element()
            Traceback (most recent call last):
            ...
            pyexactreal.cppyy_exactreal.NotRepresentableError: ...

            sage: x = R.random_element()
            sage: x / x
            1

            sage: R.random_element() / 1337
            1/1337*ℝ(...)

        """
        return self.parent()(self._backend / rhs._backend)

    def _neg_(self):
        r"""
        Return the negative of this element.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: -R.random_element()
            -ℝ(...)

        """
        return self.parent()(-self._backend)

    def __invert__(self):
        r"""
        Return the inverse of this element in its containing module.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: ~R(2)
            1/2
            sage: ~R.random_element()
            Traceback (most recent call last):
            ...
            pyexactreal.cppyy_exactreal.NotRepresentableError: result is not representable in this parent

        """
        return self.parent().one() / self

    def is_unit(self):
        r"""
        Return whether this element is a unit in its containing module.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: R.random_element().is_unit()
            False
            sage: R(2).is_unit()
            True

        """
        return self._backend.unit()

    def _floordiv_(self, other):
        r"""
        Return the integer floor of this element divided by ``other``.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: x = R.random_element()
            sage: x // x
            1
            sage: (x * x) // x == x.floor()
            True

        """
        return ZZ(self._backend.floordiv(other._backend))

    def floor(self):
        r"""
        Return the integer floor of this real number.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: x = R.random_element()
            sage: x.floor()
            0

        """
        return ZZ(self._backend.floor())

    def ceil(self):
        r"""
        Return the integer ceil of this real number.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: x = R.random_element()
            sage: x.ceil()
            1

        """
        return ZZ(self._backend.ceil())

    def __hash__(self):
        r"""
        Return a hash value for this real number.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: x = R.random_element()
            sage: hash(x) == hash(x)
            True
            sage: hash(x + 1 - 1) == hash(x)
            True

        """
        return hash(self._backend)

    def _repr_(self):
        r"""
        Return a printable representation of this element.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: R.random_element()
            ℝ(...)

        """
        return repr(self._backend)

    def _cmp_(self, rhs):
        r"""
        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: x = R.random_element() # a random element in [0, 1]
            sage: x > -x
            True
            sage: x < -x
            False
            sage: -x < x
            True
            sage: -x > x
            False
            sage: -x == -x
            True
            sage: x == -x
            False

        """
        if self._backend < rhs._backend:
            return -1
        elif self._backend == rhs._backend:
            return 0
        else:
            return 1

    def _rmul_(self, c):
        r"""
        Return the product of this element with the constant ``c``::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: R.random_element() * 1337
            1337*ℝ(...)

        """
        return self._lmul_(c)

    def _lmul_(self, c):
        r"""
        Return the product of this element with the constant ``c``::

            sage: from pyexactreal import ExactReals
            sage: R = ExactReals()
            sage: 1337 * R.random_element()
            1337*ℝ(...)

        """
        base = self.parent().base()
        if base.has_coerce_map_from(c.parent()):
            c = coerce(base, c)
            if base is QQ:
                c = cppyy.gbl.mpq_class(str(c))
            else:
                c = c.renf_elem
            return self.parent()(c * self._backend)
        else:
            # assuming that this is a module element as well
            return self.parent()(c._backend * self._backend)

class ExactReals(UniqueRepresentation, Parent):
    r"""
    The Real Numbers as a module over the number field ``base``.

    This serves as a common parent for all exact-real elements, i.e., elements
    in a finite module with transcendental or rational generators.

    EXAMPLES::

        sage: from pyexactreal import ExactReals
        sage: R = ExactReals(); R
        Real Numbers as (Rational Field)-Module
        sage: K.<a> = NumberField(x^2 - 2, embedding=AA(sqrt(2)))
        sage: RK = ExactReals(K); RK
        Real Numbers as (Number Field in a with defining polynomial x^2 - 2 with a = 1.414213562373095?)-Module

    TESTS::

        sage: R.one()._test_pickling() # first run prints some warnings from third-party C++ header files
        ...
        sage: TestSuite(R).run()
        sage: TestSuite(RK).run()

    """
    @staticmethod
    def __classcall__(cls, base=None, category=None):
        r"""
        Normalize arguments so that this is a unique parent.

        TESTS::

            sage: from pyexactreal import ExactReals
            sage: ExactReals() is ExactReals(QQ)
            True

        """
        base = base or QQ
        category = category or IntegralDomains(base).Infinite()
        return super(ExactReals, cls).__classcall__(cls, base, category)

    def __init__(self, base=None, category=None):
        if base is QQ:
            self._element_factory = exactreal.Element[type(exactreal.RationalField())]
            self._module_factory = lambda gens: QQModule(*gens)
        else:
            base = RealEmbeddedNumberField(base)
            ring = exactreal.NumberField(base.renf)
            self._element_factory = exactreal.Element[type(ring)]
            self._module_factory = lambda gens: NumberFieldModule(ring, *gens)

        Parent.__init__(self, base, category=category)
        H = Hom(base, self)
        coercion = H.__make_element_class__(CoercionExactRealsNumberField)(H)
        self.register_coercion(coercion)

    def some_elements(self):
        r"""
        Return some typical elements of this ring.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals().some_elements()
            [0,
             1,
             1,
             ℝ(0...…),
             ℝ(0...…) + 1,
             ℝ(0...…) + 1,
             ℝ(0...…) + ℝ(0...…),
             ℝ(0...…)*ℝ(0...…),
             ℝ(0...…)^2]

        """
        return [
            self.zero(),
            self.one(),
            self(self.base_ring().gen()),
            self.random_element(),
            self.random_element() + self.one(),
            self.random_element() + self.base_ring().gen(),
            self.random_element() + self.random_element(),
            self.random_element() * self.random_element(),
            self.random_element() ** 2
        ]

    def _repr_(self):
        r"""
        Return a printable represntation of this parent.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals(QQ)
            Real Numbers as (Rational Field)-Module

        """
        return "Real Numbers as (%s)-Module"%(self.base(),)

    def characteristic(self):
        r"""
        Return zero, the characteristic of the reals.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals().characteristic()
            0

        """
        return ZZ(0)

    def an_element(self):
        r"""
        Return a typical element of a finitely generated module.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals().an_element()
            0

        """
        return self(self._element_factory())

    def random_element(self, approximation=None):
        r"""
        Return a random real element.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals().random_element() # random output
            ℝ(0.303644…)

        Random elements can be created with a prescribe double approximation::

            sage: ExactReals().random_element(3.141) # random output
            ℝ(3.141=14485305783880426147p-62 + ℝ(0.778995…)p-62)

        Note that elements which approximate a double zero are extremely small
        and might not be what you want::

            sage: ExactReals().random_element(0) # random output
            ℝ(-0=-7703581330722908899p-1139 + ℝ(0.707557…)p-1139)

        We can also specify a range of doubles which should contain a random
        real::

            sage: ExactReals().random_element([1.414, 3.141]) # random output
            ℝ(2.34463=10559275352730893p-52 + ℝ(0.884672…)p-52)

        TESTS:

        Verify that the automatic seed works::

            sage: R = ExactReals()
            sage: R.random_element() != R.random_element()
            True

        """
        if approximation is None:
            generator = exactreal.RealNumber.random()
        elif isinstance(approximation, list):
            generator = exactreal.RealNumber.random(*approximation)
        else:
            generator = exactreal.RealNumber.random(approximation)

        module = self._module_factory([generator])

        return self(self._element_factory(module, [1]))

    def rational(self, q):
        r"""
        Return the rational ``q`` as the element generating the module
        generated by ``q``. Note that this is not the same as ``q`` times the
        generator of the module generated by ``1``.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: x = ExactReals().rational(2); x
            2
            sage: y = ExactReals().rational(3); y
            3
            sage: x + y
            Traceback (most recent call last):
            ...
            cppyy.gbl.std.logic_error: ... at most one generator can be rational ...

        """
        module = self._module_factory([exactreal.RealNumber.rational(q)])
        return self(self._element_factory(module, [1]))

    def is_field(self, proof=None):
        r"""
        Return whether this module is a field, i.e., return ``False``.

        In principle, when defined over a number field, one could argue this
        structure is a field since the inverse of any transcendental could show
        up as a :meth:`random_element`. However, since no field operations on
        the elements are possible, we do not claim this to be a field.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals().is_field()
            False

        """
        return False

    def is_integral_domain(self, proof=None):
        r"""
        Return whether this module is an integral domain, i.e., return ``True``.

        EXAMPLES::

            sage: from pyexactreal import ExactReals
            sage: ExactReals().is_integral_domain()
            True
            sage: ExactReals() in IntegralDomains()
            True

        """
        return True

    Element = ExactRealElement


class CoercionExactRealsNumberField(Morphism):
    r"""
    Coercion morphism from a number field to the exact reals over that number
    field.

    EXAMPLES::

        sage: from pyexactreal import ExactReals
        sage: R = ExactReals(QQ)
        sage: R.coerce_map_from(QQ)
        Generic morphism:
          From: Rational Field
          To:   Real Numbers as (Rational Field)-Module

    """
    def _call_(self, x):
        return x * self.codomain().rational(1)
