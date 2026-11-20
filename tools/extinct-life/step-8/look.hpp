#pragma once
// Scene-linear camera response: a soft toe and a hue-preserving highlight shoulder.
// Input values may exceed display white. The per-channel display transfer is a LUT.
namespace cinema {
using namespace evidence;

inline float luminance(V c){return .2126f*c.x+.7152f*c.y+.0722f*c.z;}
inline float smoother(float t){t=clamp(t);return t*t*t*(10+t*(-15+6*t));}
inline V spline(V a,V b,V c,V d,float t){
    return lerp(lerp(lerp(a,b,t),lerp(b,c,t),t),lerp(lerp(b,c,t),lerp(c,d,t),t),t);
}
struct Response {
    std::array<uint8_t,8192> lut{};
    Response(){
        for(size_t i=0;i<lut.size();i++){
            float x=float(i)/(lut.size()-1);x=x*(.89f+.11f*x/(x+.022f));
            lut[i]=uint8_t(std::round(255*(x<.0031308f?12.92f*x:1.055f*powf(x,1/2.4f)-.055f)));
        }
    }
    V press(V c)const{
        float p=std::max({c.x,c.y,c.z});
        const float knee=.57f;
        if(p>knee){
            float b=p-knee, white=knee+.43f*b/(.43f+b);
            c=lerp(c*(white/p),V{white,white,white},.24f*b/(b+1.08f));
        }
        return c;
    }
    uint8_t out(float x)const{return lut[size_t(clamp(x)*8191.f+.5f)];}
    void put(uint8_t* p,V c)const{c=press(c);p[0]=out(c.x);p[1]=out(c.y);p[2]=out(c.z);}
    uint32_t pack(V c)const{uint8_t q[3];put(q,c);return q[0]|(uint32_t(q[1])<<8)|(uint32_t(q[2])<<16);}
};
inline const Response camera_response;
}
