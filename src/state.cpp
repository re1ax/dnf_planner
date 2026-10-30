#include "dnf.hpp"
#include <sstream>
namespace dnf {
bool State::includes(const Literals&b)const{return std::includes(literals.begin(),literals.end(),b.begin(),b.end());}
bool State::contradicts(const Literals&b)const{for(auto l:b)if(literals.count(negate(l)))return true;return false;}
bool State::consistent()const{for(auto l:literals)if(literals.count(negate(l)))return false;return true;}
bool State::satisfies(const Literals&clause)const{for(auto l:clause)if(literals.count(l))return true;return false;}
bool State::goal_satisfied(const Formula&cnf)const{for(auto&c:cnf)if(!satisfies(c))return false;return true;}
bool Action::is_executable(const State&s)const{
    // 0x40d45c: impossible bodies must be explicitly refuted in each partial state.
    for(auto&c:imposs)if(!s.contradicts(c))return false;
    if(execs.empty())return true;
    for(auto&c:execs)if(s.includes(c))return true;
    return false;
}
void CState::normalize(){
    std::sort(states.begin(),states.end());states.erase(std::unique(states.begin(),states.end()),states.end());
    std::vector<State> out;
    for(size_t i=0;i<states.size();++i){
        bool redundant=false;
        for(size_t j=0;j<states.size();++j)if(i!=j && states[i].includes(states[j].literals)){redundant=true;break;}
        if(!redundant)out.push_back(states[i]);
    }
    states=std::move(out);
}
bool CState::goal_satisfied(const Formula&cnf)const{for(auto&s:states)if(!s.goal_satisfied(cnf))return false;return true;}
bool CState::is_executable(const Action&a)const{for(auto&s:states)if(!a.is_executable(s))return false;return !states.empty();}
std::string CState::key()const{
    std::ostringstream o;for(auto&s:states){for(auto l:s.literals)o<<l<<',';o<<';';}return o.str();
}
int CState::hvalue(const Formula&g)const{
    int n=0;for(auto&c:g){bool all=true;for(auto&s:states)all&=s.satisfies(c);n+=all;}return n;
}
int CState::hgvalue(const Formula&g)const{
    int n=0;for(auto&s:states){int miss=0;for(auto&c:g)miss+=!s.satisfies(c);n+=miss*miss;}return n;
}
int CState::hcvalue()const{
    if(states.empty())return 0;
    Literals common=states.front().literals;
    for(auto&s:states){Literals t;std::set_intersection(common.begin(),common.end(),s.literals.begin(),s.literals.end(),std::inserter(t,t.begin()));common=std::move(t);}
    return int(common.size());
}
}
