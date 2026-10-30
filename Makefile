CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra -Wpedantic
SOURCES = src/main.cpp src/reader.cpp src/state.cpp src/planner.cpp
dnf: $(SOURCES) src/dnf.hpp
	$(CXX) $(CXXFLAGS) $(SOURCES) -o $@
test: dnf
	python3 -m unittest discover -s tests -p 'test_*.py'
.PHONY: test
