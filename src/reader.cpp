#include "dnf.hpp"
#include <cctype>
#include <sstream>

namespace dnf {
namespace {
struct Token { std::string text; size_t line; };
class Parser {
    std::vector<Token> ts;
    size_t pos = 0;
    Reader& r;
    std::string peek() const { return ts[pos].text; }
    bool take(const std::string& s) { if(peek()==s){++pos;return true;}return false; }
    [[noreturn]] void error(const std::string& m) const {
        throw std::runtime_error("line "+std::to_string(ts[pos].line)+": "+m+" at '"+peek()+"'");
    }
    void need(const std::string& s) { if(!take(s))error("expected "+s); }
    bool identifier() const {
        return !peek().empty() && (std::isalnum((unsigned char)peek()[0]) || peek()[0]=='_' || peek()[0]=='\'');
    }
    std::string term() {
        if(!identifier())error("expected ground term");
        std::string s=ts[pos++].text;
        if(take("(")) {
            s+="(";
            if(peek()!=")") { s+=term(); while(take(","))s+=","+term(); }
            need(")");s+=")";
        }
        return s;
    }
    std::string literal() { bool neg=take("-");return (neg?"-":"")+term(); }
    std::vector<std::string> literals() {
        std::vector<std::string> out{literal()};while(take(","))out.push_back(literal());return out;
    }
    std::shared_ptr<Node> binary(Node::Kind k,std::shared_ptr<Node>a,std::shared_ptr<Node>b) {
        auto n=std::make_shared<Node>();n->kind=k;n->left=a;n->right=b;return n;
    }
    std::shared_ptr<Node> primary() {
        if(take("(")){auto n=expr();need(")");return n;}
        auto n=std::make_shared<Node>();n->kind=Node::Atom;n->label=literal();return n;
    }
    std::shared_ptr<Node> conjunction() {
        auto n=primary();while(take(","))n=binary(Node::And,n,primary());return n;
    }
    std::shared_ptr<Node> expr() {
        auto n=conjunction();while(take("|"))n=binary(Node::Or,n,conjunction());return n;
    }
public:
    Parser(Reader&rr,const std::string&s):r(rr) {
        size_t i=0,line=1;
        while(i<s.size()) {
            unsigned char c=s[i];
            if(std::isspace(c)){if(c=='\n')++line;++i;continue;}
            if(c=='#' || (c=='/' && i+1<s.size() && s[i+1]=='/')) {
                while(i<s.size()&&s[i]!='\n')++i;
                continue;
            }
            if(c=='/'&&i+1<s.size()&&s[i+1]=='*') {
                i+=2;while(i+1<s.size() && s.substr(i,2)!="*/"){if(s[i]=='\n')++line;++i;}
                if(i+1>=s.size())throw std::runtime_error("unterminated comment");
                i+=2;continue;
            }
            if(std::isalnum(c)||c=='_') {
                size_t a=i++;while(i<s.size()&&(std::isalnum((unsigned char)s[i])||s[i]=='_'))++i;
                ts.push_back({s.substr(a,i-a),line});continue;
            }
            if(c=='\'') {
                size_t a=i++;bool closed=false;
                while(i<s.size()){if(s[i++]=='\''){closed=true;break;}}
                if(!closed)throw std::runtime_error("unterminated quoted atom");
                ts.push_back({s.substr(a,i-a),line});continue;
            }
            if(std::string("-(),;|").find(c)!=std::string::npos){ts.push_back({s.substr(i++,1),line});continue;}
            throw std::runtime_error("line "+std::to_string(line)+": invalid character");
        }
        ts.push_back({"",line});
    }
    void parse() {
        while(!peek().empty()) {
            if(take("fluent")){for(auto&s:literals()){if(s[0]=='-')error("negative declaration");r.fluents.insert(s);}need(";");}
            else if(take("action")){r.actions.insert(term());while(take(","))r.actions.insert(term());need(";");}
            else if(take("initially")){auto n=expr();r.init=r.init?binary(Node::And,r.init,n):n;need(";");}
            else if(take("goal")){auto n=expr();r.goal=r.goal?binary(Node::And,r.goal,n):n;need(";");}
            else if(peek()=="executable" || peek()=="impossible") {
                bool exec=take("executable");if(!exec)need("impossible");
                auto a=term();r.actions.insert(a);std::vector<std::string>b;
                if(take("if"))b=literals();
                need(";");
                r.propositions.push_back({exec?PropositionType::Executability:PropositionType::Impossibility,a,{},b});
            } else {
                auto h=literals();
                if(take("causes")) {
                    if(h.size()!=1 || h[0][0]=='-')error("invalid action name");
                    auto a=h[0];r.actions.insert(a);auto e=literals();std::vector<std::string>b;
                    if(take("if"))b=literals();
                    need(";");
                    r.propositions.push_back({PropositionType::Dynamic,a,e,b});
                }else {
                    std::vector<std::string>b;if(take("if"))b=literals();need(";");
                    r.propositions.push_back({PropositionType::Static,"",h,b});
                }
            }
        }
        if(!r.init)throw std::runtime_error("missing initially statement");
        if(!r.goal)throw std::runtime_error("missing goal statement");
    }
};
}
void Reader::read(const std::string&text){*this=Reader{};Parser(*this,text).parse();}
}
