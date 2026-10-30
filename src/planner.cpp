#include "dnf.hpp"
#include <queue>
#include <sstream>
#include <unordered_set>

namespace dnf {
namespace {
void reduce(Formula&f,bool cnf) {
    Formula out;
    for(auto&c:f) {
        bool conflict=false;for(auto l:c)if(c.count(negate(l))){conflict=true;break;}
        if(conflict)continue; // inconsistent DNF cube / tautological CNF clause
        bool redundant=false;
        for(auto&d:out)if(std::includes(c.begin(),c.end(),d.begin(),d.end())){redundant=true;break;}
        if(redundant)continue;
        out.erase(std::remove_if(out.begin(),out.end(),[&](const Literals&d){return std::includes(d.begin(),d.end(),c.begin(),c.end());}),out.end());
        out.push_back(c);
    }
    (void)cnf;f=std::move(out);
}
}
Literal Planner::ground(const std::string&s)const {
    bool neg=!s.empty()&&s[0]=='-';std::string a=neg?s.substr(1):s;
    auto i=ids.find(a);if(i==ids.end())throw std::runtime_error("Literal "+s+" is undeclared. Check the fluent declaration.");
    return i->second+(neg?1:0);
}
Literals Planner::ground(const std::vector<std::string>&s)const{Literals r;for(auto&l:s)r.insert(ground(l));return r;}
std::string Planner::convert(Literal l)const{return (l&1?"-":"")+names.at(l/2);}
Formula Planner::normal_form(const std::shared_ptr<Node>&n,bool cnf)const {
    if(!n||n->kind==Node::True)return cnf?Formula{}:Formula{{}};
    if(n->kind==Node::False)return cnf?Formula{{}}:Formula{};
    if(n->kind==Node::Atom)return {{ground(n->label)}};
    auto a=normal_form(n->left,cnf),b=normal_form(n->right,cnf);
    bool concat=(cnf&&n->kind==Node::And)||(!cnf&&n->kind==Node::Or);
    if(concat){a.insert(a.end(),b.begin(),b.end());reduce(a,cnf);return a;}
    Formula out;
    for(auto&x:a)for(auto&y:b){
        Literals z=x;z.insert(y.begin(),y.end());out.push_back(std::move(z));
        if(out.size()>options.max_terms)throw std::runtime_error("normal form term limit exceeded");
    }
    reduce(out,cnf);return out;
}
Planner::Planner(const Reader&r,Options o):options(std::move(o)) {
    for(auto&name:r.fluents){ids[name]=static_cast<Literal>(2*names.size());names.push_back(name);}
    goal=normal_form(r.goal,true);
    for(auto&c:normal_form(r.init,false))initial.states.push_back({c});
    initial.normalize();
    if(initial.states.empty())throw std::runtime_error("inconsistent initial formula");
    std::map<std::string,size_t> amap;
    for(auto&name:r.actions){amap[name]=actions.size();actions.push_back({name,{},{},{}});}
    for(auto&p:r.propositions) {
        auto h=ground(p.head),b=ground(p.body);
        if(p.type==PropositionType::Static){statics.push_back({h,b});continue;}
        auto&a=actions.at(amap.at(p.action));
        if(p.type==PropositionType::Dynamic)a.effects.push_back({h,b});
        else if(p.type==PropositionType::Executability)a.execs.push_back(b);
        else a.imposs.push_back(b);
    }
}
CState Planner::next_cstate(const CState&from,const Action&a)const {
    if(!from.is_executable(a))throw std::runtime_error("action is not executable: "+a.name);
    struct Pending { State before; Literals effects; };
    std::vector<Pending> work;
    for(auto&s:from.states)work.push_back({s,{}});
    // 0x4148ba -> split_effect -> execute_effect: all triggers use pre-state.
    for(auto&e:a.effects) {
        std::vector<Pending> next;
        for(auto&p:work) {
            // sat_value 0x41525c also skips effects whose head is already true.
            if(p.before.includes(e.head)||p.before.contradicts(e.body)){next.push_back(p);continue;}
            Literals unknown;
            for(auto l:e.body)if(!p.before.literals.count(l))unknown.insert(l);
            if(unknown.empty()) { auto q=p;q.effects.insert(e.head.begin(),e.head.end());next.push_back(std::move(q)); }
            else {
                // The non-triggering alternatives deliberately overlap, as in split_effect.
                for(auto l:unknown){auto q=p;q.before.literals.insert(negate(l));next.push_back(std::move(q));}
                auto q=p;q.before.literals.insert(unknown.begin(),unknown.end());
                q.effects.insert(e.head.begin(),e.head.end());next.push_back(std::move(q));
            }
        }
        if(next.size()>options.max_terms)throw std::runtime_error("successor term limit exceeded");
        work=std::move(next);
    }
    CState out;
    for(auto&p:work) {
        // Ordered updates match the recovered set iteration: negative wins an
        // inconsistent pair. Such conflicting domains are not guaranteed compatible.
        for(auto l:p.effects){p.before.literals.erase(negate(l));p.before.literals.insert(l);}
        out.states.push_back(std::move(p.before));
    }
    out.normalize();return out;
}
SearchResult Planner::search()const {
    struct Entry { CState state; size_t parent; size_t action; size_t depth; };
    struct Ranked { int h, hg, hc;size_t size, serial; };
    struct Compare {
      bool alternate;
      std::shared_ptr<size_t> turn;
      bool operator()(const Ranked&a,const Ranked&b)const {
        if(alternate)++*turn;
        if(a.h!=b.h)return a.h<b.h;
        if(a.size!=b.size)return a.size>b.size;
        // The original comparator1 alternates tie breaking by call count.
        if(alternate && (*turn%2==0) && a.hc!=b.hc)return a.hc<b.hc;
        return a.hg>b.hg;
    }};
    SearchResult result;
    std::vector<Entry> entries{{initial,0,0,0}};
    const double count=double(actions.size()),literal_count=double(2*names.size());
    const double ratio=literal_count?count/literal_count:0;
    bool alternate=(ratio>20&&count<=5999)||(ratio>0.54&&ratio<0.732&&count>12&&count<=59)||
                   (ratio>1.47&&ratio<1.8&&literal_count>99&&literal_count<=1200);
    Compare comparator{alternate,std::make_shared<size_t>(0)};
    std::priority_queue<Ranked,std::vector<Ranked>,Compare> queue(comparator);
    std::unordered_set<std::string> seen{initial.key()};
    auto push=[&](size_t i){auto&s=entries[i].state;queue.push({s.hvalue(goal),s.hgvalue(goal),s.hcvalue(),s.states.size(),i});};
    push(0);auto start=std::chrono::steady_clock::now();
    auto finish=[&](size_t i){result.status=SearchResult::Found;while(i){result.plan.push_back(actions[entries[i].action].name);i=entries[i].parent;}std::reverse(result.plan.begin(),result.plan.end());};
    while(!queue.empty()) {
        if(entries.size()>options.max_nodes || std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()>options.timeout){result.status=SearchResult::Limit;return result;}
        size_t i=queue.top().serial;queue.pop();++result.explored;
        if(entries[i].state.goal_satisfied(goal)){finish(i);return result;}
        // Copy because entries can reallocate while appending successors.
        auto current=entries[i].state;auto depth=entries[i].depth;
        for(size_t ai=0;ai<actions.size();++ai) {
            const auto&a=actions[ai];if(!current.is_executable(a))continue;
            auto next=next_cstate(current,a);++result.generated;
            if(!seen.insert(next.key()).second)continue;
            entries.push_back({std::move(next),i,ai,depth+1});size_t j=entries.size()-1;
            if(entries[j].state.goal_satisfied(goal)){finish(j);return result;}
            push(j);
        }
    }
    result.status=SearchResult::Exhausted;return result;
}
void Planner::print(const CState&s,std::ostream&o)const {
    o<<"{";
    bool first=true;for(auto&c:s.states){if(!first)o<<", ";first=false;o<<"{";bool f=true;
        for(auto l:c.literals){if(!f)o<<", ";f=false;o<<convert(l);}o<<"}";
    }o<<"}";
}
bool Planner::execute(const std::vector<std::string>&plan,std::ostream&o)const {
    auto state=initial;
    for(size_t i=0;;++i) {
        o<<"STEP "<<i<<"\nCState: ";print(state,o);if(state.goal_satisfied(goal))o<<" (GOAL)";o<<"\n";
        if(i==plan.size())break;
        auto a=std::find_if(actions.begin(),actions.end(),[&](const Action&a){return a.name==plan[i];});
        if(a==actions.end())throw std::runtime_error("Could not find action "+plan[i]+" in the source file.");
        o<<"-> Action: "<<a->name<<"\n";
        if(!state.is_executable(*a)){o<<"STOP: Action "<<a->name<<" cannot be executed.\n";return false;}
        state=next_cstate(state,*a);
    }
    bool ok=state.goal_satisfied(goal);
    o<<(ok?" The tested plan is a SOLUTION!\n":" The tested plan is NOT a SOLUTION!\n");return ok;
}
}
