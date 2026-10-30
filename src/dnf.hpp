#pragma once
// Fresh reconstruction from the supplied 2013 ELF, not recovered original text.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace dnf {
using Literal = uint32_t; // positive=2*i, negative=2*i+1 (observed parity)
using Literals = std::set<Literal>;
inline Literal negate(Literal x) { return x ^ 1U; }
using Formula = std::vector<Literals>; // DNF for initial states; CNF for goals.
struct Node {
    enum Kind { Atom, And, Or, True, False } kind = True;
    std::string label;
    std::shared_ptr<Node> left, right;
};
enum class PropositionType { Static, Dynamic, Executability, Impossibility };
struct Proposition {
    PropositionType type;
    std::string action;
    std::vector<std::string> head, body;
};
struct Reader {
    std::set<std::string> fluents, actions;
    std::vector<Proposition> propositions;
    std::shared_ptr<Node> init, goal;
    void read(const std::string& text);
};
struct State {
    Literals literals;
    bool includes(const Literals&) const;
    bool contradicts(const Literals&) const;
    bool consistent() const;
    bool satisfies(const Literals& clause) const;
    bool goal_satisfied(const Formula& cnf) const;
    bool operator<(const State& b) const { return literals < b.literals; }
    bool operator==(const State& b) const { return literals == b.literals; }
};
struct Effect { Literals head, body; };
struct Action {
    std::string name;
    std::vector<Literals> execs, imposs;
    std::vector<Effect> effects;
    bool is_executable(const State&) const;
};
struct CState {
    std::vector<State> states;
    void normalize();
    bool goal_satisfied(const Formula&) const;
    bool is_executable(const Action&) const;
    std::string key() const;
    int hvalue(const Formula&) const;
    int hgvalue(const Formula&) const;
    int hcvalue() const;
};
struct Options {
    bool print_states = false;
    size_t max_nodes = 200000;
    size_t max_terms = 1000000;
    double timeout = 60;
    std::string semantics = "pc";
};
struct SearchResult {
    enum Status { Found, Exhausted, Limit } status = Exhausted;
    std::vector<std::string> plan;
    size_t generated = 0, explored = 0;
};
class Planner {
public:
    explicit Planner(const Reader& r, Options o = {});
    CState initial;
    Formula goal;
    std::vector<Action> actions;
    std::vector<Effect> statics;
    std::vector<std::string> names;
    Options options;
    Literal ground(const std::string&) const;
    std::string convert(Literal) const;
    CState next_cstate(const CState&, const Action&) const;
    SearchResult search() const;
    bool execute(const std::vector<std::string>& plan, std::ostream& out) const;
    void print(const CState&, std::ostream&) const;
private:
    std::map<std::string,Literal> ids;
    Formula normal_form(const std::shared_ptr<Node>&, bool cnf) const;
    Literals ground(const std::vector<std::string>&) const;
};
} // namespace dnf
