#include "dnf.hpp"
#include <fstream>
#include <sstream>
#include <cctype>

static std::string read_file(const std::string&path){
    std::ifstream f(path);if(!f)throw std::runtime_error("File "+path+" cannot be opened.");
    return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};
}
static void usage(){
    std::cout<<"USAGE: dnf input_domain [options]\n"
             <<"  -e action1 action2 ...   Execute a plan\n"
             <<"  -t FILENAME             Read original unprefixed plan format\n"
             <<"  -pc / -ph               Original option names (same verified core)\n"
             <<"  -p / -o                 Accepted legacy flags; see compatibility notes\n"
             <<"  --plan FILENAME         Read one exact AL action per line\n"
             <<"  --max-nodes N           Search node limit (default 200000)\n"
             <<"  --timeout SECONDS       Search time limit (default 60)\n";
}
int main(int argc,char**argv){
    using namespace dnf;
    try {
        std::cout<<"DNF reconstructed from 2013 distribution\n";
        if(argc<2){usage();return 1;}
        if(std::string(argv[1])=="--help"){usage();return 0;}
        Options options;std::vector<std::string> plan;bool execute=false;
        for(int i=2;i<argc;++i){
            std::string arg=argv[i];
            auto value=[&](){if(i+1>=argc)throw std::runtime_error("missing value after "+arg);return std::string(argv[++i]);};
            if(arg=="-e"){
                execute=true;while(i+1<argc&&argv[i+1][0]!='-')plan.push_back(argv[++i]);
            }else if(arg=="--plan"||arg=="-t"){
                execute=true;std::istringstream in(read_file(value()));std::string line;
                while(std::getline(in,line)){
                    std::istringstream words(line);std::string a,w;if(!(words>>a))continue;
                    if(arg=="-t"){
                        a="cpa_"+a;bool first=true;while(words>>w){a+=(first?"(cpa_":",cpa_")+w;first=false;}if(!first)a+=")";
                    }else{
                        a=line;
                        a.erase(std::remove_if(a.begin(),a.end(),[](unsigned char c){return std::isspace(c);}),a.end());
                    }
                    plan.push_back(a);
                }
            }else if(arg=="-pc")options.semantics="pc";
            else if(arg=="-ph")options.semantics="ph";
            else if(arg=="-p"||arg=="-o"){} // Original flags retained; no unsupported optimization claim.
            else if(arg=="--max-nodes")options.max_nodes=std::stoull(value());
            else if(arg=="--timeout")options.timeout=std::stod(value());
            else throw std::runtime_error("unknown option "+arg);
        }
        Reader r;r.read(read_file(argv[1]));Planner p(r,options);
        if(execute){p.execute(plan,std::cout);return 0;}
        auto result=p.search();
        if(result.status==SearchResult::Found){
            std::cout<<"Found a plan\n";for(size_t i=0;i<result.plan.size();++i)std::cout<<i+1<<": "<<result.plan[i]<<"\n";
            std::cout<<"Length: "<<result.plan.size()<<"\n";
        }else if(result.status==SearchResult::Exhausted)std::cout<<"No plan was found.\n";
        else {std::cout<<"Search limit reached; existence of a plan remains unknown.\n";return 2;}
        std::cout<<"Total DNF-states generated "<<result.generated<<"\nTotal DNF-states explored "<<result.explored<<"\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}
}
