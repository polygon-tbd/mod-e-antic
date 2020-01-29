/**********************************************************************
 *  This file is part of exact-real.
 *
 *        Copyright (C) 2019 Vincent Delecroix
 *        Copyright (C) 2019 Julian Rüth
 *
 *  exact-real is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  exact-real is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with exact-real. If not, see <https://www.gnu.org/licenses/>.
 *********************************************************************/

#include <e-antic/renfxx.h>
#include <boost/lexical_cast.hpp>

#include "external/catch2/single_include/catch2/catch.hpp"

#include "../exact-real/element.hpp"
#include "../exact-real/integer_ring.hpp"
#include "../exact-real/module.hpp"
#include "../exact-real/number_field.hpp"
#include "../exact-real/rational_field.hpp"
#include "../exact-real/real_number.hpp"

using boost::lexical_cast;
using eantic::renf_class;
using eantic::renf_elem_class;
using std::make_shared;
using std::shared_ptr;
using std::string;
using std::vector;

namespace exactreal::test {

TEST_CASE("Elements from Primitives", "[element]") {
  auto m = Module<RationalField>::make({RealNumber::rational(1), RealNumber::random()});
  auto x = m->gen(1);

  auto one = Element(1);
  auto zero = Element(0);
  auto quot = Element(mpq_class(1, 2));

  // Check that arithmetic works with elements from different trivial rings
  REQUIRE(one + zero == one);
  REQUIRE(quot + zero == quot);
  REQUIRE(quot + one == one + quot);

  REQUIRE(x + zero == x);
  REQUIRE(x + one - one == x);
  REQUIRE(x + quot + quot == x + one);

  // Comparison between different parents in trivial cases
  REQUIRE(quot - quot == zero);
  REQUIRE(quot + quot == one);
  REQUIRE(x - x == zero);
  REQUIRE(x + one - x == one);
}

TEST_CASE("Element over ZZ", "[element][integer_ring]") {
  auto m = Module<IntegerRing>::make({RealNumber::rational(1), RealNumber::random()});

  auto one = m->gen(0);
  auto x = m->gen(1);
  auto zero = m->zero();
  auto trivial = Element<IntegerRing>();

  SECTION("Relational Operators") {
    REQUIRE(one == one);
    REQUIRE(x == x);
    REQUIRE(x == m->gen(1));
    REQUIRE(one != x);
    REQUIRE(x > m->zero());
    REQUIRE(x < one);

    REQUIRE(x[0] == 0);
    REQUIRE(x[1] == 1);
  }

  SECTION("Additive Structure") {
    Element<IntegerRing> elements[]{one, x};

    for (size_t i = 0; i < sizeof(elements) / sizeof(one); i++) {
      auto x = elements[i];
      REQUIRE(x + elements[0] > x);
      REQUIRE(x + elements[0] > elements[0]);
      REQUIRE(x - elements[i] == m->zero());
    }
  }

  SECTION("Promotion from Trivial Elements") {
    REQUIRE(zero == trivial);
    REQUIRE(x != trivial);

    REQUIRE(x + trivial == x);
    REQUIRE(zero + trivial == zero);
    REQUIRE(0 * x == trivial);
    REQUIRE(x >= trivial);
  }

  SECTION("Promotion from Submodule") {
    auto n = Module<IntegerRing>::make({RealNumber::rational(1)});

    REQUIRE(n->gen(0) == one);
    REQUIRE(n->gen(0) != x);
    REQUIRE(&*(n->gen(0) + one).module() == &*m);
  }

  SECTION("Arithmetic with Scalars") {
    Element<IntegerRing> elements[]{one, x};

    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == 2 * x);
      REQUIRE(x - x == 0 * x);
      REQUIRE(-1 * x == -x);
      REQUIRE(1 * x == x);
      REQUIRE(0 * x == m->zero());
      REQUIRE(Element<IntegerRing>() * x == Element<IntegerRing>());
    }

    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == mpz_class(2) * x);
      REQUIRE(mpz_class(2) * x > x);
      REQUIRE(x - x == mpz_class(0) * x);
      REQUIRE(mpz_class(-1) * x == -x);
      REQUIRE(mpz_class(-1) * x < x);
      REQUIRE(mpz_class(-1) * x < m->zero());
      auto one = RealNumber::rational(1);
      REQUIRE(mpz_class(-1) * x < *one);
      if (i == 0)
        REQUIRE(x == *one);
      else
        REQUIRE(x != *one);
      REQUIRE(mpz_class(1) * x == x);
      REQUIRE(mpz_class(0) * x == m->zero());
    }
  }

  SECTION("Printing") {
    REQUIRE(lexical_cast<string>(m->gen(0)) == "1");
    REQUIRE(lexical_cast<string>(m->gen(1)) == "ℝ(0.982253…)");
    REQUIRE(lexical_cast<string>(m->gen(0) + m->gen(1)) == "ℝ(0.982253…) + 1");
  }

  SECTION("Multiplication") {
    REQUIRE(one * one == one);
    REQUIRE(one * x == x);
    REQUIRE(x * x != x);
    REQUIRE(x * x == x * x);
    REQUIRE(x - x * one == one - one);
  }

  SECTION("Coefficients") {
    REQUIRE(one.coefficients<mpq_class>() == std::vector<mpq_class>({1, 0}));
    REQUIRE(x.coefficients<mpq_class>() == std::vector<mpq_class>({0, 1}));
  }
}

TEST_CASE("Element over QQ", "[element][rational_field]") {
  auto m = Module<RationalField>::make({RealNumber::rational(1), RealNumber::random()});

  Element<RationalField> elements[]{m->gen(0), m->gen(1)};

  SECTION("Scalars") {
    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == 2 * x);
      REQUIRE(x - x == 0 * x);
      REQUIRE(-1 * x == -x);
      REQUIRE(1 * x == x);
      REQUIRE(0 * x == m->zero());
      REQUIRE(Element<RationalField>() * x == Element<RationalField>());
    }

    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == mpz_class(2) * x);
      REQUIRE(mpz_class(2) * x > x);
      REQUIRE(x - x == mpz_class(0) * x);
      REQUIRE(mpz_class(-1) * x == -x);
      REQUIRE(mpz_class(-1) * x < x);
      REQUIRE(mpz_class(-1) * x < m->zero());
      auto one = RealNumber::rational(1);
      REQUIRE(mpz_class(-1) * x < *one);
      if (i == 0)
        REQUIRE(x == *one);
      else
        REQUIRE(x != *one);
      REQUIRE(mpz_class(1) * x == x);
      REQUIRE(mpz_class(0) * x == m->zero());
    }

    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == mpq_class(2) * x);
      REQUIRE(x - x == mpq_class(0) * x);
      REQUIRE(mpq_class(-1) * x == -x);
      REQUIRE(mpq_class(1) * x == x);
      REQUIRE(mpq_class(0) * x == m->zero());
    }
  }
}

TEST_CASE("Elements over Number Field", "[element][number_field]") {
  auto K = renf_class::make("a^2 - 2", "a", "1.41 +/- 0.1", 64);
  auto m = Module<NumberField>::make({RealNumber::rational(1), RealNumber::random()}, K);

  auto x = m->gen(1);
  auto a = renf_elem_class(K, "a");

  Element<NumberField> elements[]{m->gen(0), x};

  SECTION("Scalars") {
    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == 2 * x);
      REQUIRE(x - x == 0 * x);
      REQUIRE(-1 * x == -x);
      REQUIRE(1 * x == x);
      REQUIRE(0 * x == m->zero());
      REQUIRE(Element<NumberField>() * x == Element<NumberField>());
    }

    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == mpz_class(2) * x);
      REQUIRE(mpz_class(2) * x > x);
      REQUIRE(x - x == mpz_class(0) * x);
      REQUIRE(mpz_class(-1) * x == -x);
      REQUIRE(mpz_class(-1) * x < x);
      REQUIRE(mpz_class(-1) * x < m->zero());
      auto one = RealNumber::rational(1);
      REQUIRE(mpz_class(-1) * x < *one);
      if (i == 0)
        REQUIRE(x == *one);
      else
        REQUIRE(x != *one);
      REQUIRE(mpz_class(1) * x == x);
      REQUIRE(mpz_class(0) * x == m->zero());
    }

    for (size_t i = 0; i < sizeof(elements) / sizeof(elements[0]); i++) {
      auto x = elements[i];
      REQUIRE(x + x == renf_elem_class(K, 2) * x);
      REQUIRE(x - x == renf_elem_class(K, 0) * x);
      REQUIRE(renf_elem_class(K, -1) * x == -x);
      REQUIRE(renf_elem_class(K, 1) * x == x);
      REQUIRE(renf_elem_class(K, 0) * x == m->zero());
      REQUIRE(-(renf_elem_class(K, "a") * x) == renf_elem_class(K, "-a") * x);
      REQUIRE(renf_elem_class(K, "a") * x > x);
      REQUIRE(2 * x > renf_elem_class(K, "a") * x);
      REQUIRE(mpq_class(1, 2) * x == x / 2);

      for (size_t j = 0; j < sizeof(elements) / sizeof(elements[0]); j++) {
        if (i == j)
          REQUIRE((x + x) / elements[j] == 2);
        else
          REQUIRE((x + x) / elements[j] == std::optional<renf_elem_class>{});
      }
    }
  }

  SECTION("Coefficients") {
    REQUIRE(x.coefficients() == std::vector<renf_elem_class>({0, 1}));
    REQUIRE((a * x).coefficients() == std::vector<renf_elem_class>({0, a}));

    REQUIRE(x.coefficients<mpq_class>() == std::vector<mpq_class>({0, 0, 1, 0}));
    REQUIRE((a * x).coefficients<mpq_class>() == std::vector<mpq_class>({0, 0, 0, 1}));

    auto rationals = Module<NumberField>::make({RealNumber::rational(1)});
    REQUIRE(rationals->zero().coefficients<mpq_class>() == std::vector<mpq_class>(1, 0));
    REQUIRE(rationals->gen(0).coefficients<mpq_class>() == std::vector<mpq_class>(1, 1));
  }
}

}  // namespace exactreal::test
